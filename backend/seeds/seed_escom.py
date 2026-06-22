"""Seed inicial de ESCOM-IPN.

Pobla:
  * Usuarios de prueba con los 4 roles (RF009).
  * Edificios reales de ESCOM con su nomenclatura ABCD:
    A = edificio (1-4, edif. labs comparte 3xxx/4xxx según lado, gobierno aparte).
    B = piso (0 PB, 1 P1, 2 P2).
    CD = número de salón (01-14).
  * Access Points distribuidos por aula con bandas mixtas.
  * Configuración de umbrales por defecto.

Ejecutar con:
    python -m seeds.seed_escom

Idempotente: detecta seeds previos por código y los omite.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AccessPoint,
    Aula,
    BandaFrecuencia,
    ConfiguracionUmbrales,
    Edificio,
    Piso,
    RolUsuario,
    Usuario,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# --- Usuarios demo ----------------------------------------------------------
USUARIOS_SEMILLA = [
    {
        "correo": "alosaurio777@gmail.com",
        "nombre_completo": "Administrador TI Demo",
        "password": "admin1234",
        "rol": RolUsuario.ADMINISTRADOR_TI,
    },
    {
        "correo": "tecnico1@escom.ipn.mx",
        "nombre_completo": "Pedro González (Soporte)",
        "password": "tecnico1234",
        "rol": RolUsuario.PERSONAL_TECNICO,
    },
    {
        "correo": "docente1@escom.ipn.mx",
        "nombre_completo": "Dra. Laura Méndez",
        "password": "docente1234",
        "rol": RolUsuario.DOCENTE,
    },
    {
        "correo": "estudiante1@escom.ipn.mx",
        "nombre_completo": "Alumno Demo",
        "password": "alumno1234",
        "rol": RolUsuario.ESTUDIANTE,
    },
]


# --- Helpers de construcción ------------------------------------------------
def aulas(prefijo: int, start: int, end: int, *, tipo: str = "aula") -> list[dict[str, Any]]:
    """Genera aulas correlativas con el patrón <prefijo><cd 2 dígitos>."""
    return [{"codigo": f"{prefijo}{i:02d}", "tipo": tipo} for i in range(start, end + 1)]


# --- Catálogo de edificios reales de ESCOM ---------------------------------
# Coordenadas aproximadas (centroides en la huella real del campus de
# Zacatenco según OpenStreetMap). El campus está ligeramente rotado
# respecto al norte geográfico; OSM siempre dibuja con norte arriba, así
# que los marcadores reflejan la posición geográfica real, no la
# orientación del mapa estilizado de ESCOM. Para afinar: clic derecho
# sobre un edificio en openstreetmap.org → "Mostrar dirección" → copiar
# lat/lon aquí.
EDIFICIOS_ESCOM: list[dict[str, Any]] = [
    {
        "codigo": "ED1",
        "nombre": "Edificio 1",
        "descripcion": "Salones y laboratorios — lado este, norte del campus.",
        "latitud": 19.505032,
        "longitud": -99.147067,
        "pisos": [
            {
                "numero": 0,
                "nombre": "Planta Baja",
                "aulas": aulas(10, 1, 14, tipo="aula"),  # 1001-1014
            },
            {
                "numero": 1,
                "nombre": "Primer Piso",
                "aulas": [
                    {"codigo": "1101", "nombre": "Unidad de Informática", "tipo": "unidad_informatica"},
                    {"codigo": "1102", "nombre": "Aula de Computadoras", "tipo": "computo"},
                    {"codigo": "1103", "tipo": "laboratorio"},
                    {"codigo": "1104", "tipo": "laboratorio"},
                    {"codigo": "1105", "tipo": "laboratorio"},
                    {"codigo": "1106", "tipo": "cubiculo"},
                    *aulas(11, 7, 14, tipo="aula"),  # 1107-1114
                ],
            },
            {
                "numero": 2,
                "nombre": "Segundo Piso",
                "aulas": aulas(12, 1, 14, tipo="aula"),  # 1201-1214
            },
        ],
    },
    {
        "codigo": "ED2",
        "nombre": "Edificio 2",
        "descripcion": "Salones, posgrado y laboratorios — lado oeste, norte del campus.",
        "latitud": 19.504788,
        "longitud": -99.146396,
        "pisos": [
            {
                "numero": 0,
                "nombre": "Planta Baja",
                "aulas": [
                    *aulas(20, 1, 7, tipo="aula"),  # 2001-2007
                    *aulas(20, 8, 14, tipo="posgrado"),  # 2008-2014 posgrado
                ],
            },
            {
                "numero": 1,
                "nombre": "Primer Piso",
                "aulas": [
                    {"codigo": "2101", "tipo": "cubiculo"},
                    *aulas(21, 2, 7, tipo="laboratorio"),  # 2102-2107
                    *aulas(21, 8, 14, tipo="posgrado"),  # 2108-2114
                ],
            },
            {
                "numero": 2,
                "nombre": "Segundo Piso",
                "aulas": aulas(22, 1, 14, tipo="aula"),  # 2201-2214
            },
        ],
    },
    {
        "codigo": "ED3",
        "nombre": "Edificio 3",
        "descripcion": "Salones — lado este, centro del campus.",
        "latitud": 19.504119,
        "longitud": -99.147208,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": aulas(30, 8, 13, tipo="aula")},
            {"numero": 1, "nombre": "Primer Piso", "aulas": aulas(31, 8, 13, tipo="aula")},
            {"numero": 2, "nombre": "Segundo Piso", "aulas": aulas(32, 8, 13, tipo="aula")},
        ],
    },
    {
        "codigo": "ED4",
        "nombre": "Edificio 4",
        "descripcion": "Salones — lado oeste, centro del campus.",
        "latitud": 19.504087,
        "longitud": -99.147075,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": aulas(40, 8, 13, tipo="aula")},
            {"numero": 1, "nombre": "Primer Piso", "aulas": aulas(41, 8, 13, tipo="aula")},
            {"numero": 2, "nombre": "Segundo Piso", "aulas": aulas(42, 8, 13, tipo="aula")},
        ],
    },
    {
        "codigo": "LABS",
        "nombre": "Edificio de Laboratorios",
        "descripcion": (
            "Edificio central de laboratorios, zona sur del campus. "
            "La nomenclatura comparte prefijos con los edificios 3 y 4 "
            "según el lado: lado derecho usa 3xxx, lado izquierdo usa 4xxx."
        ),
        "latitud": 19.504691,
        "longitud": -99.146830,
        "pisos": [
            {
                "numero": 0,
                "nombre": "Planta Baja",
                "aulas": [
                    # Lado derecho (3xxx)
                    *aulas(30, 1, 7, tipo="laboratorio"),  # 3001-3007
                    # Lado izquierdo (4xxx)
                    *aulas(40, 1, 7, tipo="laboratorio"),  # 4001-4007
                ],
            },
            {
                "numero": 1,
                "nombre": "Primer Piso",
                "aulas": [
                    *aulas(31, 1, 7, tipo="cubiculo"),  # 3101-3107
                    *aulas(41, 1, 7, tipo="cubiculo"),  # 4101-4107
                ],
            },
            {
                "numero": 2,
                "nombre": "Segundo Piso",
                "aulas": [
                    *aulas(32, 1, 7, tipo="cubiculo"),  # 3201-3207
                    *aulas(42, 1, 7, tipo="cubiculo"),  # 4201-4207
                ],
            },
        ],
    },
    {
        "codigo": "GOB",
        "nombre": "Edificio de Gobierno",
        "descripcion": "Personal administrativo y gestión escolar. Al norte del campus, junto al acceso principal.",
        "latitud": 19.505226,
        "longitud": -99.146567,
        "pisos": [
            {
                "numero": 0,
                "nombre": "Planta Baja",
                "aulas": [
                    {"codigo": "GOB-CUB", "nombre": "Cubículos de Gobierno", "tipo": "administracion"},
                    {"codigo": "GOB-BIB", "nombre": "Biblioteca", "tipo": "biblioteca"},
                    {"codigo": "GOB-AUD", "nombre": "Auditorio", "tipo": "auditorio"},
                ],
            },
        ],
    },
    {
        "codigo": "PAL-GOB",
        "nombre": "Palapas de Gestión",
        "descripcion": "Área de palapas junto a Gestión Escolar.",
        "latitud": 19.505561,
        "longitud": -99.146849,
        "pisos": [],
    },
    {
        "codigo": "PAL-IA",
        "nombre": "Palapas de IA",
        "descripcion": "Área de palapas zona sur del campus.",
        "latitud": 19.503650,
        "longitud": -99.146527,
        "pisos": [],
    },
]


# --- Implementación del seed ------------------------------------------------
def _seed_usuarios(session) -> None:
    for datos in USUARIOS_SEMILLA:
        # Para el admin buscamos por rol (permite actualizar correo en re-seed).
        if datos["rol"] == RolUsuario.ADMINISTRADOR_TI:
            existe = session.scalar(select(Usuario).where(Usuario.rol == RolUsuario.ADMINISTRADOR_TI))
            if existe:
                if existe.correo != datos["correo"]:
                    existe.correo = datos["correo"]
                    logger.info("Admin actualizado: correo → %s", datos["correo"])
                continue
        else:
            existe = session.scalar(select(Usuario).where(Usuario.correo == datos["correo"]))
            if existe:
                continue
        session.add(
            Usuario(
                correo=datos["correo"],
                nombre_completo=datos["nombre_completo"],
                password_hash=hash_password(datos["password"]),
                rol=datos["rol"],
            )
        )
        logger.info("Usuario creado: %s (%s)", datos["correo"], datos["rol"].value)


def _seed_ubicaciones_y_aps(session) -> None:
    bandas = [BandaFrecuencia.DUAL, BandaFrecuencia.GHZ_5, BandaFrecuencia.GHZ_2_4]

    for edif_data in EDIFICIOS_ESCOM:
        edificio = session.scalar(
            select(Edificio).where(Edificio.codigo == edif_data["codigo"])
        )
        if not edificio:
            edificio = Edificio(
                codigo=edif_data["codigo"],
                nombre=edif_data["nombre"],
                descripcion=edif_data["descripcion"],
                latitud=edif_data["latitud"],
                longitud=edif_data["longitud"],
            )
            session.add(edificio)
            session.flush()
            logger.info("Edificio creado: %s", edificio.codigo)

        for piso_data in edif_data["pisos"]:
            piso = session.scalar(
                select(Piso).where(
                    Piso.edificio_id == edificio.id,
                    Piso.numero == piso_data["numero"],
                )
            )
            if not piso:
                piso = Piso(
                    edificio_id=edificio.id,
                    numero=piso_data["numero"],
                    nombre=piso_data["nombre"],
                )
                session.add(piso)
                session.flush()

            for idx, aula_data in enumerate(piso_data["aulas"]):
                aula = session.scalar(
                    select(Aula).where(
                        Aula.piso_id == piso.id, Aula.codigo == aula_data["codigo"]
                    )
                )
                if not aula:
                    aula = Aula(
                        piso_id=piso.id,
                        codigo=aula_data["codigo"],
                        nombre=aula_data.get("nombre"),
                        tipo=aula_data.get("tipo", "aula"),
                    )
                    session.add(aula)
                    session.flush()

                ap_codigo = f"AP-{edif_data['codigo']}-{aula_data['codigo']}"
                if session.scalar(select(AccessPoint).where(AccessPoint.codigo == ap_codigo)):
                    continue
                session.add(
                    AccessPoint(
                        codigo=ap_codigo,
                        nombre=f"AP {aula_data['codigo']}",
                        modelo="Cisco Catalyst 9120AX",
                        aula_id=aula.id,
                        banda=bandas[idx % len(bandas)],
                    )
                )


def _seed_configuracion(session) -> None:
    existe = session.scalar(select(ConfiguracionUmbrales).limit(1))
    if existe:
        return
    session.add(ConfiguracionUmbrales())
    logger.info("Configuración de umbrales por defecto creada.")


def main() -> None:
    with SessionLocal() as session:
        _seed_usuarios(session)
        _seed_ubicaciones_y_aps(session)
        _seed_configuracion(session)
        session.commit()
    logger.info("Seed de ESCOM completado correctamente.")


if __name__ == "__main__":
    main()
