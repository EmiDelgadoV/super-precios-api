import pytest


@pytest.fixture()
def categoria(client, auth_headers):
    return client.post(
        "/categories/", params={"name": "Lacteos"}, headers=auth_headers
    ).json()


def test_crear_producto_aparece_en_listado(client, auth_headers, categoria):
    respuesta = client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    )
    assert respuesta.status_code == 200
    producto = respuesta.json()
    assert producto["name"] == "Leche"
    assert producto["category_id"] == categoria["id"]

    listado = client.get("/products/", headers=auth_headers).json()
    assert "Leche" in [p["name"] for p in listado]


def test_editar_producto_cambia_nombre_y_categoria(client, auth_headers, categoria):
    otra_categoria = client.post(
        "/categories/", params={"name": "Bebidas"}, headers=auth_headers
    ).json()
    producto = client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    ).json()

    respuesta = client.put(
        f"/products/{producto['id']}",
        params={"name": "Leche Entera", "category_id": otra_categoria["id"]},
        headers=auth_headers,
    )
    assert respuesta.status_code == 200
    actualizado = respuesta.json()
    assert actualizado["name"] == "Leche Entera"
    assert actualizado["category_id"] == otra_categoria["id"]


def test_eliminar_producto_borra_sus_precios(client, auth_headers, categoria):
    producto = client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    ).json()
    comercio = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    ).json()
    client.post(
        "/prices/",
        json={"product_id": producto["id"], "store_id": comercio["id"], "amount": 1000},
        headers=auth_headers,
    )

    respuesta = client.delete(f"/products/{producto['id']}", headers=auth_headers)
    assert respuesta.status_code == 200

    # El producto ya no existe...
    assert client.get(f"/products/{producto['id']}", headers=auth_headers).status_code == 404

    # ...y su precio tampoco quedo huerfano en el comercio
    vista_comercio = client.get(f"/stores/{comercio['id']}/prices", headers=auth_headers).json()
    assert vista_comercio["prices"] == []


def test_producto_duplicado_en_misma_categoria_rechazado(client, auth_headers, categoria):
    client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    )
    respuesta = client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    )
    assert respuesta.status_code == 400


def test_crear_producto_con_categoria_inexistente(client, auth_headers):
    respuesta = client.post(
        "/products/",
        params={"name": "Leche", "category_id": 9999},
        headers=auth_headers,
    )
    assert respuesta.status_code == 404
