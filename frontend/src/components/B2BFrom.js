import { useState } from "react";
import axios from "axios";

export default function SearchForm() {
  const [product, setProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [maxPrice, setMaxPrice] = useState("");
  const [result, setResult] = useState(null);

  const handleSearch = async () => {
    try {
      const res = await axios.post("http://localhost:8000/search", {
        product_name: product,
        quantity,
        max_price: maxPrice ? parseFloat(maxPrice) : null,
      });

      console.log("API Response:", res.data); // Debug API response
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Error fetching results");
    }
  };

  const renderBestProduct = () => {
    if (!result || !result.best_product) return <p>No products found for your search.</p>;

    const best = result.best_product;

    return (
      <div style={{ marginTop: "20px" }}>
        <h3>Best Product: {best.product_name || "N/A"}</h3>
        <p>Supplier: {best.supplier_name || "N/A"}</p>
        <p>Price: {best.total_price != null ? best.total_price + " TND" : "N/A"}</p>
        <p>Explanation: {result.explanation || "No explanation available"}</p>

        {result.alternatives && result.alternatives.length > 0 && (
          <>
            <h3>Alternative Suppliers</h3>
            <ul>
              {result.alternatives.map((alt, idx) => (
                <li key={idx}>
                  {alt.product_name || "N/A"} - {alt.total_price != null ? alt.total_price + " TND" : "N/A"} ({alt.supplier_name || "N/A"})
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    );
  };

  return (
    <div>
      <h2>Search Best Supplier</h2>
      <input
        type="text"
        placeholder="Product name"
        value={product}
        onChange={(e) => setProduct(e.target.value)}
      />
      <input
        type="number"
        placeholder="Quantity"
        min={1}
        value={quantity}
        onChange={(e) => setQuantity(parseInt(e.target.value))}
      />
      <input
        type="number"
        placeholder="Max price (optional)"
        value={maxPrice}
        onChange={(e) => setMaxPrice(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>

      {renderBestProduct()}
    </div>
  );
}
