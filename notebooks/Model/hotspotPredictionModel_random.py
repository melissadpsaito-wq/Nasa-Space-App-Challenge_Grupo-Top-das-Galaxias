import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


df = pd.read_parquet("dataset_model_ready_2016_2025.parquet")

# Definindo X (Variáveis explicativas) e y (O que queremos prever)

colunas_para_excluir = [
    "cell",
    "monthly_frp",
]  
X = df.drop(columns=colunas_para_excluir)
y = df["monthly_frp"]

print("Dividindo os dados em treino e teste ...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.05, random_state=42
)

# Criando o modelo com paralelismo máximo (usa todos os núcleos do seu processador)
print("Treinando o modelo Random Forest...")
modelo_random = RandomForestRegressor(
    n_estimators=100,  # Quantidade de árvores de decisão
    max_depth=15,  # Limite de profundidade para evitar que decore demais (overfitting)
    n_jobs=-1,  # Usa 100% da CPU
    random_state=42,
)

# O treinamento em si (a IA aprende os padrões)
modelo_random.fit(X_train, y_train)
print("Modelo treinado com sucesso!")

print("📊 Avaliando a performance do modelo nos dados de teste...")
y_pred = modelo_random.predict(X_test)

r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"\n📈 Resultados da Avaliação:")
print(f"- Coeficiente R² (Acurácia explicativa): {r2:.4f}")
print(f"- RMSE (Erro Médio): {rmse:.4f}")

# Salvando o modelo treinado em disco
arquivo_modelo = "modelo_fogo_random_forest_95_5.pkl"
joblib.dump(modelo_random, arquivo_modelo)
print(f"💾 Modelo salvo com sucesso no arquivo '{arquivo_modelo}'!")