def test_crear_categoria_aparece_en_el_listado(client, auth_headers):
    respuesta = client.post(
        "/categories/", params={"name": "Panificados"}, headers=auth_headers
    )
    assert respuesta.status_code == 200

    categoria = respuesta.json()
    assert categoria["name"] == "Panificados"
    assert categoria["code"] == "PAN"
    assert categoria["product_count"] == 0

    listado = client.get("/categories/", headers=auth_headers)
    assert listado.status_code == 200
    nombres = [c["name"] for c in listado.json()]
    assert "Panificados" in nombres


def test_categorias_exige_login(client):
    respuesta = client.get("/categories/")
    assert respuesta.status_code == 401
