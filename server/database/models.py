from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey

Base = declarative_base()

class Operadora(Base):
    __tablename__ = 'operadoras'
    registro_ans = Column(String(20), primary_key=True)
    cnpj = Column(String(18))
    razao_social = Column(String(255))
    # Adicione outros campos conforme necessário

class Demonstracao(Base):
    __tablename__ = 'demonstracoes'
    id = Column(Integer, primary_key=True)
    registro_ans = Column(String(20), ForeignKey('operadoras.registro_ans'))
    descricao = Column(String(255))
    valor = Column(Numeric(15, 2))
    trimestre = Column(Integer)
    ano = Column(Integer)