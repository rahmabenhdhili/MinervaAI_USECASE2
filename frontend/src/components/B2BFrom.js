import { useState } from "react";
import axios from "axios";

export default function SearchForm() {
  const [product, setProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [maxPrice, setMaxPrice] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    // Validation formulaire
    if (!product || !quantity || !maxPrice) {
      setError("Tous les champs sont obligatoires pour lancer la recherche.");
      return;
    }

    if (quantity <= 0 || maxPrice <= 0) {
      setError("La quantité et le budget maximum doivent être supérieurs à zéro.");
      return;
    }

    setError(""); // reset erreur

    try {
      const res = await axios.post("http://localhost:8000/search", {
        product_name: product,
        quantity,
        max_price: parseFloat(maxPrice),
      });

      console.log("API Response:", res.data);

      // Stocker le produit et le prix utilisés pour la recherche
      setResult({
        ...res.data,
        searched_product: product,
        searched_maxPrice: maxPrice,
      });
    } catch (err) {
      console.error(err);
      setError("Erreur lors de la récupération des résultats.");
    }
  };

  const renderBestProduct = () => {
    if (!result) return null;

    // Cas : aucun produit trouvé
    if (result.explanation === "No products match your criteria.") {
      return (
        <div
          style={{
            marginTop: 30,
            padding: 20,
            border: "1px solid #f44336",
            borderRadius: 8,
            backgroundColor: "#fdecea",
            color: "#b71c1c",
          }}
        >
          <strong>
            Aucun fournisseur correspondant à{" "}
            <em>{result.searched_product}</em> trouvé dans le budget de prix max{" "}
            <em>{result.searched_maxPrice || "∞"}</em> TND
          </strong>
        </div>
      );
    }

    const best = result.best_product;

    return (
      <div style={{ marginTop: 30 }}>
        {/* ===== MEILLEUR CHOIX ===== */}
        <div className="card card-best">
          <h2>Meilleur choix</h2>
          <div className="best-total-price">{best.total_price} TND</div>

          <h3>{best.product_name}</h3>

          <div className="best-card-container">
            <div className="best-mini-card">
              <strong>Fournisseur</strong>
              {best.supplier_name}
            </div>
            <div className="best-mini-card">
              <strong>Ville</strong>
              {best.city}
            </div>
            <div className="best-mini-card">
              <strong>Marque</strong>
              {best.brand}
            </div>
            <div className="best-mini-card">
              <strong>Prix unitaire</strong>
              {best.unit_price} TND
            </div>
            <div className="best-mini-card">
              <strong>Quantité</strong>
              {quantity}
            </div>
            <div className="best-mini-card">
              <strong>Téléphone</strong>
              {best.phone}
            </div>
            <div className="best-mini-card">
              <strong>Email</strong>
              {best.email}
            </div>
          </div>

          {/* Explication */}
          {result.explanation &&
            result.explanation !== "No products match your criteria." && (
              <div className="explanation-card">
                <h4>Pourquoi ce choix ?</h4>
                <p>{result.explanation}</p>
              </div>
            )}
        </div>

        {/* ===== ALTERNATIVES ===== */}
        {result.alternatives && result.alternatives.length > 0 && (
          <div style={{ marginTop: 25 }}>
            <h3>Alternatives</h3>
            {result.alternatives.map((alt, idx) => (
              <div key={idx} className="card card-alt">
                <h4>{alt.product_name}</h4>
                <div className="alt-info">
                  <p>
                    <strong>Fournisseur:</strong> {alt.supplier_name}
                  </p>
                  <p>
                    <strong>Ville:</strong> {alt.city}
                  </p>
                  <p>
                    <strong>Marque:</strong> {alt.brand}
                  </p>
                  <p>
                    <strong>Contact:</strong> {alt.phone} | {alt.email}
                  </p>
                  <p>
                    <strong>Prix unitaire:</strong> {alt.unit_price} TND
                  </p>
                  <p>
                    <strong>Quantité:</strong> {quantity}
                  </p>
                </div>
                <div className="alt-total-price">{alt.total_price} TND</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="form-group">
        <label>Que cherchez-vous ?</label>
        <input
          type="text"
          placeholder="Ex: ordinateur portable, cahier, papier A4..."
          value={product}
          onChange={(e) => setProduct(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Quantité</label>
        <input
          type="number"
          min={1}
          placeholder="Ex: 10"
          value={quantity}
          onChange={(e) => setQuantity(parseInt(e.target.value))}
        />
      </div>

      <div className="form-group">
        <label>Budget maximum (TND)</label>
        <input
          type="number"
          placeholder="Ex: 5000"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />
      </div>

      <button
        onClick={handleSearch}
        disabled={!product || !quantity || !maxPrice}
      >
        Rechercher
      </button>

      {error && (
        <div className="form-error" style={{ color: "red", marginTop: 10 }}>
          {error}
        </div>
      )}

      {renderBestProduct()}
    </div>
  );
}
