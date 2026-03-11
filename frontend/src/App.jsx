import { BrowserRouter, Routes, Route } from "react-router-dom";

function Home() {
  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>AI Career Assistant</h1>
      <p>Your intelligent platform for career growth.</p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
