import { render, screen } from "@testing-library/react";
import Home from "../app/page";
import { vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock("@/app/hooks/useAuth", () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}));

describe("Home page", () => {
  it("renders the project name", () => {
    render(<Home />);

    expect(screen.getByText("COLA-ZERO")).toBeInTheDocument();
  });
});

