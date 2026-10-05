import pytest


@pytest.fixture()
def producto_y_comercios(client, auth_headers):
    """Una categoria, un producto y dos comercios, listos para cargarles precios."""
    categoria = client.post(
        "/categories/", params={"name": "Lacteos"}, headers=auth_headers
    ).json()
    producto = client.post(
        "/products/",
        params={"name": "LecheProteica", "category_id": categoria["id"]},
        headers=auth_headers,
    ).json()
    beraca = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    ).json()
    vea = client.post(
        "/stores/", params={"name": "Vea", "number": 2}, headers=auth_headers
    ).json()
    return {"producto": producto, "beraca": beraca, "vea": vea}


def test_cargar_precio_lo_marca_como_mas_barato(client, auth_headers, producto_y_comercios):
    p = producto_y_comercios
    respuesta = client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 4500},
        headers=auth_headers,
    )
    assert respuesta.status_code == 200

    detalle = client.get(f"/products/{p['producto']['id']}", headers=auth_headers).json()
    assert len(detalle["prices"]) == 1
    assert detalle["prices"][0]["is_cheapest"] == 1


def test_precio_mas_bajo_en_otro_comercio_cambia_el_mas_barato(
    client, auth_headers, producto_y_comercios
):
    p = producto_y_comercios
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 4500},
        headers=auth_headers,
    )
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["vea"]["id"], "amount": 4200},
        headers=auth_headers,
    )

    detalle = client.get(f"/products/{p['producto']['id']}", headers=auth_headers).json()
    por_comercio = {pr["store_name"]: pr for pr in detalle["prices"]}

    assert por_comercio["Vea"]["is_cheapest"] == 1
    assert por_comercio["Beraca"]["is_cheapest"] == 0

    # La vista de Beraca tiene que avisar donde esta mas barato ahora
    vista_beraca = client.get(
        f"/stores/{p['beraca']['id']}/prices", headers=auth_headers
    ).json()
    item = vista_beraca["prices"][0]
    assert item["is_cheapest"] is False
    assert item["cheapest_store"] == "Vea"
    assert item["cheapest_amount"] == 4200


def test_actualizar_precio_guarda_el_anterior(client, auth_headers, producto_y_comercios):
    p = producto_y_comercios
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 4500},
        headers=auth_headers,
    )
    respuesta = client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 4700},
        headers=auth_headers,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["precio_anterior"] == 4500
    assert respuesta.json()["precio_nuevo"] == 4700

    # previous_amount se expone en el listado, no en el detalle de un producto
    listado = client.get("/products/", headers=auth_headers).json()
    producto = next(x for x in listado if x["id"] == p["producto"]["id"])
    assert producto["prices"][0]["amount"] == 4700
    assert producto["prices"][0]["previous_amount"] == 4500


def test_precio_por_kg_se_recalcula_aunque_no_se_reenvie_la_cantidad(
    client, auth_headers, producto_y_comercios
):
    p = producto_y_comercios
    # Primera carga: con cantidad (1 kg = 1000 g, segun la formula del proyecto)
    client.post(
        "/prices/",
        json={
            "product_id": p["producto"]["id"],
            "store_id": p["beraca"]["id"],
            "amount": 1000,
            "quantity": 1000,
        },
        headers=auth_headers,
    )
    # Segunda carga: mismo precio nuevo, sin mandar quantity de nuevo
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 2000},
        headers=auth_headers,
    )

    detalle = client.get(f"/products/{p['producto']['id']}", headers=auth_headers).json()
    # Antes de este arreglo, unit_price se quedaba con el valor viejo (1000.0)
    assert detalle["prices"][0]["unit_price"] == 2000.0


def test_precio_en_cero_no_gana_como_mas_barato(client, auth_headers, producto_y_comercios):
    p = producto_y_comercios
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["beraca"]["id"], "amount": 0},
        headers=auth_headers,
    )
    client.post(
        "/prices/",
        json={"product_id": p["producto"]["id"], "store_id": p["vea"]["id"], "amount": 3000},
        headers=auth_headers,
    )

    detalle = client.get(f"/products/{p['producto']['id']}", headers=auth_headers).json()
    por_comercio = {pr["store_name"]: pr for pr in detalle["prices"]}

    assert por_comercio["Beraca"]["is_cheapest"] == 0
    assert por_comercio["Vea"]["is_cheapest"] == 1
