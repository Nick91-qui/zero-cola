import { render, screen, waitFor } from "@testing-library/react";
import OmrHomePage from "../app/omr/page";
import ExamsListPage from "../app/exams/page";
import { vi } from "vitest";
import * as omrLib from "@/lib/omr";
import * as examsLib from "@/lib/exams";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useParams: () => ({ templateId: "123", examId: "456" }),
}));

vi.mock("@/app/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { email: "teacher@cola-zero.edu", role: "teacher" },
    isAuthenticated: true,
    isLoading: false,
    logout: vi.fn(),
  }),
}));

describe("OMR and Exams UI Pages", () => {
  it("renders OMR home page with named template list", async () => {
    vi.spyOn(omrLib, "listTemplates").mockResolvedValue([
      {
        id: "tmpl-1",
        title: "Prova de Química – Ligações Químicas",
        exam_id: "exam-1",
        layout_version: "v1_std_20q",
        total_questions: 20,
        options_per_question: 5,
        correct_answers: { "1": "A" },
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(<OmrHomePage />);

    await waitFor(() => {
      expect(screen.getByText("Prova de Química – Ligações Químicas")).toBeInTheDocument();
    });
  });

  it("renders Exams list page with exam title and class filter", async () => {
    vi.spyOn(examsLib, "listExams").mockResolvedValue([
      {
        id: "exam-1",
        title: "Avaliação Diagnóstica de Matemática",
        description: "1º Bimestre",
        teacher_id: "teacher-1",
        class_id: "301",
        omr_template_id: "tmpl-1",
        total_questions: 20,
        max_score: 10.0,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(<ExamsListPage />);

    await waitFor(() => {
      expect(screen.getByText("Avaliação Diagnóstica de Matemática")).toBeInTheDocument();
      expect(screen.getByText("Turma 301")).toBeInTheDocument();
    });
  });
});
