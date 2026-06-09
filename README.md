# 📦 Sistema de Controle de Estoque Profissional

Este é um sistema completo de controle de estoque baseado em linha de comando (CLI) desenvolvido em **Python**. O projeto utiliza **SQLite** para persistência de dados local e segue padrões arquiteturais de mercado para garantir um código limpo, modular e de fácil manutenção.

## 🚀 Funcionalidades
- **Cadastro de Produtos:** Armazenamento persistente com geração automática de IDs (Autoincremento).
- **Entrada de Estoque:** Atualização de quantidades para compras ou reposições.
- **Saída de Estoque:** Registro de vendas ou baixas com validação para impedir estoque negativo.
- **Relatório Consolidado:** Tabela formatada que exibe o saldo de cada item e calcula o valor total do patrimônio em estoque.

## 🛠️ Diferenciais Técnicos (Boas Práticas)
- **Repository Pattern:** Separação clara entre a lógica de banco de dados (SQL) e as regras de negócio.
- **Service Layer:** Validações centralizadas que garantem a integridade dos dados.
- **Context Managers (`with`):** Controle seguro das conexões com o banco de dados para evitar vazamento de memória.
- **Tratamento de Exceções:** O sistema não quebra caso o usuário digite letras em campos numéricos ou tente duplicar produtos.

## 🔧 Como Executar o Projeto

1. Certifique-se de ter o **Python 3** instalado em sua máquina.
2. Clone este repositório ou baixe os arquivos.
3. Abra o terminal na pasta do projeto e execute:
   ```bash
   python app.py
