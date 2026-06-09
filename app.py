import os
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional

# =====================================================================
# 1. CAMADA DE CONFIGURAÇÃO E BANCO DE DADOS (DATABASE)
# =====================================================================

DB_NAME = "estoque.db"

@contextmanager
def obter_conexao():
    """Gerencia a conexão com o SQLite garantindo o fechamento seguro."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def inicializar_banco():
    """Cria a tabela de estoque caso ela não exista no sistema."""
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                quantidade INTEGER NOT NULL DEFAULT 0,
                preco REAL NOT NULL
            )
        """)
        conn.commit()


# =====================================================================
# 2. CAMADA DE MODELO DE DOMÍNIO (MODEL)
# =====================================================================

@dataclass
class Produto:
    """Representação clara da entidade Produto utilizando boas práticas."""
    nome: str
    quantidade: int
    preco: float
    id: Optional[int] = None

    def calcular_valor_total(self) -> float:
        return self.quantidade * self.preco


# =====================================================================
# 3. CAMADA DE ACESSO AOS DADOS (REPOSITORY PATTERN)
# =====================================================================

class ProdutoRepository:
    """Isola completamente as instruções SQL do restante da lógica."""
    
    @staticmethod
    def criar(produto: Produto) -> int:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO produtos (nome, quantidade, preco) VALUES (?, ?, ?)",
                (produto.nome, produto.quantidade, produto.preco)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def buscar_por_id(id_prod: int) -> Optional[Produto]:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (id_prod,))
            row = cursor.fetchone()
            if row:
                return Produto(id=row["id"], nome=row["nome"], quantidade=row["quantidade"], preco=row["preco"])
            return None

    @staticmethod
    def listar_todos() -> List[Produto]:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produtos")
            rows = cursor.fetchall()
            return [Produto(id=row["id"], nome=row["nome"], quantidade=row["quantidade"], preco=row["preco"]) for row in rows]

    @staticmethod
    def atualizar_quantidade(id_prod: int, nova_qtd: int) -> None:
        with obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, id_prod))
            conn.commit()


# =====================================================================
# 4. CAMADA DE REGRAS DE NEGÓCIO (SERVICE)
# =====================================================================

class EstoqueService:
    """Garante que as regras de negócio (como validações) sejam cumpridas."""
    
    def __init__(self):
        self.repository = ProdutoRepository()

    def cadastrar_produto(self, nome: str, quantidade: int, preco: float) -> Produto:
        if not nome.strip():
            raise ValueError("O nome do produto não pode estar em branco.")
        if quantidade < 0 or preco < 0:
            raise ValueError("Quantidade e preço não podem ser valores negativos.")
        
        novo_produto = Produto(nome=nome.strip(), quantidade=quantidade, preco=preco)
        try:
            novo_produto.id = self.repository.criar(novo_produto)
            return novo_produto
        except sqlite3.IntegrityError:
            raise ValueError(f"Já existe um produto cadastrado com o nome '{nome}'.")

    def registrar_entrada(self, id_prod: int, quantidade: int) -> Produto:
        if quantidade <= 0:
            raise ValueError("A quantidade de entrada deve ser maior que zero.")
        
        produto = self.repository.buscar_por_id(id_prod)
        if not produto:
            raise ValueError("Produto não encontrado com o ID informado.")
        
        nova_qtd = produto.quantidade + quantidade
        self.repository.atualizar_quantidade(id_prod, nova_qtd)
        produto.quantidade = nova_qtd
        return produto

    def registrar_saida(self, id_prod: int, quantidade: int) -> Produto:
        if quantidade <= 0:
            raise ValueError("A quantidade de saída deve ser maior que zero.")
        
        produto = self.repository.buscar_por_id(id_prod)
        if not produto:
            raise ValueError("Produto não encontrado com o ID informado.")
        
        if produto.quantidade < quantidade:
            raise ValueError(f"Estoque insuficiente. Quantidade atual disponível: {produto.quantidade}")
            
        nova_qtd = produto.quantidade - quantidade
        self.repository.atualizar_quantidade(id_prod, nova_qtd)
        produto.quantidade = nova_qtd
        return produto

    def listar_estoque(self) -> List[Produto]:
        return self.repository.listar_todos()


# =====================================================================
# 5. CAMADA DE INTERFACE (CLI INTERACTION)
# =====================================================================

class SistemaEstoqueCLI:
    """Interface de usuário via linha de comando."""
    
    def __init__(self):
        inicializar_banco()
        self.service = EstoqueService()

    def limpar_tela(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def executar(self):
        while True:
            print("\n" + "="*50)
            print("📦 SISTEMA DE GESTÃO DE ESTOQUE PROFISSIONAL")
            print("="*50)
            print("1. ➕ Cadastrar Novo Produto")
            print("2. 📥 Registrar Entrada (Compra/Abastecimento)")
            print("3. 📤 Registrar Saída (Venda/Baixa)")
            print("4. 📋 Exibir Relatório Consolidado")
            print("5. ❌ Sair do Sistema")
            print("="*50)
            
            opcao = input("Selecione uma opção (1-5): ").strip()
            
            try:
                if opcao == "1":
                    self.limpar_tela()
                    print("--- CADASTRO DE PRODUTO ---")
                    nome = input("Nome do produto: ")
                    qtd = int(input("Quantidade inicial em estoque: "))
                    preco = float(input("Preço unitário: R$ "))
                    p = self.service.cadastrar_produto(nome, qtd, preco)
                    print(f"\n✔️ Sucesso: '{p.nome}' cadastrado com o ID {p.id}!")
                
                elif opcao == "2":
                    self.limpar_tela()
                    print("--- ENTRADA DE PRODUTO ---")
                    id_prod = int(input("Digite o ID do produto: "))
                    qtd = int(input("Quantidade adicionada: "))
                    p = self.service.registrar_entrada(id_prod, qtd)
                    print(f"\n✔️ Sucesso: Estoque de '{p.nome}' atualizado para {p.quantidade}.")
                    
                elif opcao == "3":
                    self.limpar_tela()
                    print("--- SAÍDA DE PRODUTO ---")
                    id_prod = int(input("Digite o ID do produto: "))
                    qtd = int(input("Quantidade retirada: "))
                    p = self.service.registrar_saida(id_prod, qtd)
                    print(f"\n✔️ Sucesso: Estoque de '{p.nome}' atualizado para {p.quantidade}.")
                    
                elif opcao == "4":
                    self.limpar_tela()
                    produtos = self.service.listar_estoque()
                    if not produtos:
                        print("\nℹ️ O estoque está totalmente vazio no momento.")
                        continue
                    
                    print("\n--- RELATÓRIO ATUAL DE ESTOQUE ---")
                    print(f"{'ID':<5} | {'Nome do Produto':<25} | {'Qtd':<6} | {'Preço Unit.':<12} | {'Total R$':<12}")
                    print("-" * 70)
                    
                    total_financeiro = 0.0
                    for p in produtos:
                        total_p = p.calcular_valor_total()
                        total_financeiro += total_p
                        print(f"{p.id:<5} | {p.nome:<25} | {p.quantidade:<6} | R$ {p.preco:<9.2f} | R$ {total_p:<9.2f}")
                    
                    print("-" * 70)
                    print(f"VALOR TOTAL DO PATRIMÔNIO EM ESTOQUE: R$ {total_financeiro:.2f}")

                elif opcao == "5":
                    print("\nEncerrando o sistema de forma segura... Até logo!")
                    sys.exit(0)
                else:
                    print("\n⚠️ Opção inválida! Escolha um número entre 1 e 5.")
            
            except ValueError as e:
                print(f"\n❌ Erro de Validação: {e}")
            except Exception as e:
                print(f"\n❌ Erro Crítico do Sistema: {e}")

            input("\nPressione Enter para voltar ao menu principal...")
            self.limpar_tela()


if __name__ == "__main__":
    app = SistemaEstoqueCLI()
    app.executar()