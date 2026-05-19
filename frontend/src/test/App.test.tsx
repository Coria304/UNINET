import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import App from "@/App";

const renderApp = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>,
  );
};

describe("App", () => {
  it("redirige a /login cuando no hay sesión", () => {
    renderApp();
    expect(
      screen.getByRole("heading", { name: /UniNet Connect/i }),
    ).toBeInTheDocument();
  });
});
