"""Pruebas de API e integración para configuración de usuario."""




def test_list_preferences_empty(client):
    """Sin preferencias guardadas, devuelve lista vacía."""
    response = client.get("/api/v1/settings/preferences")
    assert response.status_code == 200
    assert response.json() == []


def test_set_and_get_theme(client):
    """Se puede establecer y obtener el tema."""
    response = client.put("/api/v1/settings/theme", json={"theme": "dark"})
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"

    response = client.get("/api/v1/settings/theme")
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


def test_set_theme_invalid_rejected(client):
    """Tema inválido es rechazado."""
    response = client.put("/api/v1/settings/theme", json={"theme": "neon"})
    assert response.status_code == 400


def test_set_and_get_timezone(client):
    """Se puede establecer y obtener la zona horaria."""
    response = client.put(
        "/api/v1/settings/timezone", json={"timezone": "America/Argentina/Cordoba"}
    )
    assert response.status_code == 200
    assert response.json()["timezone"] == "America/Argentina/Cordoba"

    response = client.get("/api/v1/settings/timezone")
    assert response.status_code == 200
    assert response.json()["timezone"] == "America/Argentina/Cordoba"


def test_set_timezone_empty_rejected(client):
    """Zona horaria vacía es rechazada."""
    response = client.put("/api/v1/settings/timezone", json={"timezone": ""})
    assert response.status_code == 400


def test_set_preference_generic(client):
    """Se puede establecer una preferencia genérica por clave/valor."""
    response = client.put(
        "/api/v1/settings/preferences/language", json={"value": "es"}
    )
    assert response.status_code == 200
    assert response.json()["key"] == "language"
    assert response.json()["value"] == "es"

    response = client.get("/api/v1/settings/preferences")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["key"] == "language"
    assert data[0]["value"] == "es"


def test_theme_defaults_to_system(client):
    """El tema por defecto es 'system' cuando no está configurado."""
    response = client.get("/api/v1/settings/theme")
    assert response.status_code == 200
    assert response.json()["theme"] == "system"


def test_timezone_defaults_to_arg_cordoba(client):
    """La zona horaria por defecto es America/Argentina/Cordoba."""
    response = client.get("/api/v1/settings/timezone")
    assert response.status_code == 200
    assert response.json()["timezone"] == "America/Argentina/Cordoba"