import React from "react";
import ReactDOM from "react-dom/client";
import "reactflow/dist/style.css";
import { App } from "./App";
import "./styles.css";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("#root element missing");
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
