import './App.css';
import SearchForm from './components/B2BFrom';

function App() {
  return (
    <div
      className="App"
      style={{
        background: "#f0f2f5",
        minHeight: "100vh",
        padding: "40px 20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Header principal */}
      <header style={{ textAlign: "center", marginBottom: "40px", maxWidth: "800px" }}>
        <h1 style={{ color: "#2c3e50", fontSize: "36px", fontWeight: "700", marginBottom: "10px" }}>
          Dinero - B2B Service
        </h1>
        <p style={{ color: "#34495e", fontSize: "18px", lineHeight: "1.5" }}>
          Trouvez les meilleurs fournisseurs tunisiens au meilleur prix
        </p>
      </header>

      {/* Formulaire de recherche */}
      <div style={{ width: "100%", maxWidth: "800px" }}>
        <SearchForm />
      </div>
    </div>
  );
}

export default App;
