import pytest


@pytest.fixture()
def headers_otro_usuario(client):
    """Una segunda cuenta, distinta de la que crea auth_headers."""
    email = "otro@test.com"
    password = "clave1234"
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post(
        "/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_otro_usuario_no_ve_nada_de_la_cuenta_original(
    client, auth_headers, headers_otro_usuario
):
    client.post("/categories/", params={"name": "Lacteos"}, headers=auth_headers)
    client.post("/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers)

    assert client.get("/categories/", headers=headers_otro_usuario).json() == []
    assert client.get("/products/", headers=headers_otro_usuario).json() == []
    assert client.get("/stores/", headers=headers_otro_usuario).json() == []


def test_otro_usuario_no_puede_editar_ni_borrar_por_id_directo(
    client, auth_headers, headers_otro_usuario
):
    categoria = client.post(
        "/categories/", params={"name": "Lacteos"}, headers=auth_headers
    ).json()
    producto = client.post(
        "/products/",
        params={"name": "Leche", "category_id": categoria["id"]},
        headers=auth_headers,
    ).json()
    comercio = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    ).json()

    # Categoria: ni editar ni borrar
    assert client.put(
        f"/categories/{categoria['id']}", params={"name": "Hackeada"}, headers=headers_otro_usuario
    ).status_code == 404
    assert client.delete(
        f"/categories/{categoria['id']}", headers=headers_otro_usuario
    ).status_code == 404

    # Producto: ni ver, ni editar, ni borrar
    assert client.get(f"/products/{producto['id']}", headers=headers_otro_usuario).status_code == 404
    assert client.put(
        f"/products/{producto['id']}",
        params={"name": "Hackeado", "category_id": categoria["id"]},
        headers=headers_otro_usuario,
    ).status_code == 404
    assert client.delete(
        f"/products/{producto['id']}", headers=headers_otro_usuario
    ).status_code == 404

    # Comercio: ni ver, ni editar, ni borrar
    assert client.get(f"/stores/{comercio['id']}", headers=headers_otro_usuario).status_code == 404
    assert client.put(
        f"/stores/{comercio['id']}", params={"name": "Hackeado", "number": 99}, headers=headers_otro_usuario
    ).status_code == 404
    assert client.delete(
        f"/stores/{comercio['id']}", headers=headers_otro_usuario
    ).status_code == 404

    # Precio: no puede cargar uno usando IDs que no le pertenecen
    respuesta = client.post(
        "/prices/",
        json={"product_id": producto["id"], "store_id": comercio["id"], "amount": 100},
        headers=headers_otro_usuario,
    )
    assert respuesta.status_code == 404


def test_mismo_numero_de_comercio_en_cuentas_distintas_no_choca(
    client, auth_headers, headers_otro_usuario
):
    uno = client.post(
        "/stores/", params={"name": "Beraca", "number": 1}, headers=auth_headers
    )
    otro = client.post(
        "/stores/", params={"name": "Otro Beraca", "number": 1}, headers=headers_otro_usuario
    )
    assert uno.status_code == 200
    assert otro.status_code == 200
