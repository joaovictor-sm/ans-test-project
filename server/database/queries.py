from .config import SessionLocal
from .models import Operadora, Demonstracao
from sqlalchemy import func, and_

def get_top_operadoras_trimestre():
    db = SessionLocal()
    try:
        return db.query(
            Operadora.razao_social,
            func.sum(Demonstracao.valor).label('total')
        ).join(Demonstracao).filter(
            and_(
                Demonstracao.descricao.ilike('%EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS%'),
                Demonstracao.trimestre == 4,
                Demonstracao.ano == 2023
            )
        ).group_by(Operadora.razao_social
        ).order_by(func.sum(Demonstracao.valor).desc()
        ).limit(10).all()
    finally:
        db.close()

def get_top_operadoras_ano():
    db = SessionLocal()
    try:
        return db.query(
            Operadora.razao_social,
            func.sum(Demonstracao.valor).label('total')
        ).join(Demonstracao).filter(
            and_(
                Demonstracao.descricao.ilike('%EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS%'),
                Demonstracao.ano == 2023
            )
        ).group_by(Operadora.razao_social
        ).order_by(func.sum(Demonstracao.valor).desc()
        ).limit(10).all()
    finally:
        db.close()