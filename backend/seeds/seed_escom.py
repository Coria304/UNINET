"""Seed inicial de ESCOM-IPN.

Pobla:
  * Usuarios de prueba con los 4 roles.
  * Edificios principales de ESCOM (1, 2, 3, 4) con pisos y aulas.
  * Access Points distribuidos por aula con bandas mixtas.
  * Configuración de umbrales por defecto.

Ejecutar con:
    docker compose exec backend python -m seeds.seed_escom

Idempotente: detecta seeds previos por código y los omite.
"""

from __future__ import annotations

import logging

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


# --- Datos de referencia ----------------------------------------------------
USUARIOS_SEMILLA = [
    {
        "correo": "admin.ti@escom.ipn.mx",
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

EDIFICIOS_ESCOM = [
    {
        "codigo": "ED1",
        "nombre": "Edificio 1 — Aulas",
        "descripcion": "Aulas teóricas y oficinas administrativas.",
        "latitud": 19.5046,
        "longitud": -99.1467,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": ["1100", "1101", "1102", "1103"]},
            {"numero": 1, "nombre": "Piso 1", "aulas": ["1200", "1201", "1202", "1203"]},
            {"numero": 2, "nombre": "Piso 2", "aulas": ["1300", "1301", "1302", "1303"]},
            {"numero": 3, "nombre": "Piso 3", "aulas": ["1400", "1401", "1402", "1403"]},
        ],
    },
    {
        "codigo": "ED2",
        "nombre": "Edificio 2 — Laboratorios",
        "descripcion": "Laboratorios de cómputo y redes.",
        "latitud": 19.5048,
        "longitud": -99.1465,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": ["LAB1", "LAB2", "LAB3"]},
            {"numero": 1, "nombre": "Piso 1", "aulas": ["LAB4", "LAB5", "LAB6"]},
            {"numero": 2, "nombre": "Piso 2", "aulas": ["LAB7", "LAB8"]},
        ],
    },
    {
        "codigo": "ED3",
        "nombre": "Edificio 3 — Investigación",
        "descripcion": "Posgrado e investigación.",
        "latitud": 19.5050,
        "longitud": -99.1463,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": ["AULA_MAGNA", "BIBLIOTECA"]},
            {"numero": 1, "nombre": "Piso 1", "aulas": ["POS1", "POS2"]},
        ],
    },
    {
        "codigo": "ED4",
        "nombre": "Edificio 4 — Aulas Avanzadas",
        "descripcion": "Aulas inteligentes y áreas comunes.",
        "latitud": 19.5044,
        "longitud": -99.1469,
        "pisos": [
            {"numero": 0, "nombre": "Planta Baja", "aulas": ["CAFETERIA", "AREA_COMUN"]},
            {"numero": 1, "nombre": "Piso 1", "aulas": ["4100", "4101"]},
            {"numero": 2, "nombre": "Piso 2", "aulas": ["4200", "4201"]},
        ],
    },
]


def _seed_usuarios(session) -> None:
    for datos in USUARIOS_SEMILLA:
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

            for idx, codigo_aula in enumerate(piso_data["aulas"]):
                aula = session.scalar(
                    select(Aula).where(Aula.piso_id == piso.id, Aula.codigo == codigo_aula)
                )
                if not aula:
                    aula = Aula(
                        piso_id=piso.id,
                        codigo=codigo_aula,
                        nombre=codigo_aula,
                        tipo="laboratorio" if "LAB" in codigo_aula else "aula",
                    )
                    session.add(aula)
                    session.flush()

                ap_codigo = f"AP-{edif_data['codigo']}-{piso_data['numero']}-{codigo_aula}"
                if session.scalar(select(AccessPoint).where(AccessPoint.codigo == ap_codigo)):
                    continue
                session.add(
                    AccessPoint(
                        codigo=ap_codigo,
                        nombre=f"AP {codigo_aula}",
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
