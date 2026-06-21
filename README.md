# 📊 Dashboard Estatístico — Shiny for Python

Dashboard interativo construído com [Shiny for Python](https://shiny.posit.co/py/) para análise estatística de dados quantitativos. Permite carregar arquivos CSV/Excel e realizar análise descritiva, testes de hipóteses, intervalos de confiança e regressão linear simples, tudo em uma interface web.

## ✨ Funcionalidades

### 1. Análise Descritiva
- Upload de arquivos `.csv`, `.xlsx` ou `.xls`
- Detecção automática de separador, codificação e formato decimal em CSVs
- Conversão automática de colunas de texto para numéricas (incluindo valores com unidades, ex: `"5 km/h"`)
- Extração automática de coordenadas no formato `"lat, lon"` em colunas separadas
- Histograma e boxplot da variável selecionada
- Tabela de estatísticas descritivas (média, mediana, desvio-padrão, n, mínimo, máximo)
- Pré-visualização dos dados carregados

### 2. Teste de Hipóteses (Teste Z — variância conhecida)
- Testes bilateral, unilateral à direita e unilateral à esquerda
- Configuração de variância populacional, valor de μ₀ e nível de significância (α)
- Cálculo automático da estatística Z, p-valor e decisão (rejeitar/não rejeitar H₀)

### 3. Intervalo de Confiança
- Intervalo de confiança normal para a média (σ² conhecida)
- Nível de confiança ajustável

### 4. Regressão Linear Simples
- Gráfico de dispersão com reta ajustada
- Coeficientes de correlação (R) e determinação (R²)
- p-valor da inclinação, erro-padrão e equação da reta

## 🛠️ Tecnologias

- [Shiny for Python](https://shiny.posit.co/py/)
- [pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [SciPy](https://scipy.org/) (`scipy.stats`)
- [Matplotlib](https://matplotlib.org/)

## 📦 Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd <nome-do-repositorio>

# (Opcional) crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install shiny pandas numpy scipy matplotlib
```

## ▶️ Como executar

```bash
shiny run --reload dashboard.py
```

Depois, acesse no navegador o endereço exibido no terminal (geralmente `http://127.0.0.1:8000`).

## 📁 Formatos de arquivo suportados

O dashboard tenta automaticamente diferentes combinações de separador, decimal e codificação ao ler arquivos CSV:

| Separador | Decimal | Codificação |
|-----------|---------|--------------|
| `;`       | `,`     | utf-8        |
| `;`       | `,`     | latin-1      |
| `,`       | `.`     | utf-8        |
| `,`       | `.`     | latin-1      |
| `\t`      | `,`     | utf-8        |

Se nenhuma combinação funcionar, o sistema tenta inferir o separador automaticamente.

## 📋 Como usar

1. Acesse a aba **Análise Descritiva**
2. Faça upload de um arquivo CSV ou Excel e clique em **📂 Carregar Dados**
3. Selecione a variável quantitativa de interesse na barra lateral
4. Navegue pelas abas:
   - **Teste de Hipóteses**: configure μ₀, σ², tipo de teste e α
   - **Intervalo de Confiança**: ajuste o nível de confiança e σ²
   - **Regressão Linear**: selecione as variáveis x (explicativa) e y (resposta)

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

Copyright (c) 2026 Luiz Eduardo
