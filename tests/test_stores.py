def test_crear_comercio_aparece_en_listado(client, auth_headers):
    respuesta = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    )
    assert respuesta.status_code == 200
    comercio = respuesta.json()
    assert comercio["name"] == "Beraca"
    assert comercio["number"] == 1

    listado = client.get("/stores/", headers=auth_headers).json()
    assert "Beraca" in [s["name"] for s in listado]


def test_editar_comercio_cambia_nombre_y_numero(client, auth_headers):
    comercio = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    ).json()

    respuesta = client.put(
        f"/stores/{comercio['id']}",
        params={"name": "Beraca Centro", "number": 5},
        headers=auth_headers,
    )
    assert respuesta.status_code == 200
    actualizado = respuesta.json()
    assert actualizado["name"] == "Beraca Centro"
    assert actualizado["number"] == 5


def test_numero_de_comercio_duplicado_rechazado(client, auth_headers):
    client.post("/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers)
    respuesta = client.post(
        "/stores/", params={"name": "Otro", "number": 1}, headers=auth_headers
    )
    assert respuesta.status_code == 400


def test_eliminar_comercio_recalcula_el_mas_barato(client, auth_headers):
    """
    Reproduce el caso real que probamos a mano con LecheProteica: si se
    elimina el comercio que tenia el precio mas barato, el producto tiene
    que quedar marcado como mas barato en el comercio que le sigue.
    """
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

    client.post(
        "/prices/",
        json={"product_id": producto["id"], "store_id": beraca["id"], "amount": 4500},
        headers=auth_headers,
    )
    client.post(
        "/prices/",
        json={"product_id": producto["id"], "store_id": vea["id"], "amount": 4700},
        headers=auth_headers,
    )

    respuesta = client.delete(f"/stores/{beraca['id']}", headers=auth_headers)
    assert respuesta.status_code == 200

    detalle = client.get(f"/products/{producto['id']}", headers=auth_headers).json()
    assert len(detalle["prices"]) == 1
    assert detalle["prices"][0]["store_name"] == "Vea"
    assert detalle["prices"][0]["is_cheapest"] == 1
