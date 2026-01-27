from load_data_B2B import load_products
from embedding_agent_B2B import EmbeddingAgent

if __name__ == "__main__":
    products = load_products("../data/suppliers.csv")
    agent = EmbeddingAgent()
    agent.index_products(products)
