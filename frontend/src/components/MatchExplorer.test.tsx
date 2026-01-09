import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MatchExplorer from "./MatchExplorer";

const mockMatches = [
  {
    definition: "test verb 1",
    class: "Ia",
    strictness: "strict",
    scope: "full",
    stem_final_match_present: "True",
    stem_final_match_imperfective: "True",
    stem_final_match_perfective: "True",
    stem_final_match_imperative: "True",
    stem_final_match_infinitive: "True",
  },
  {
    definition: "test verb 2",
    class: "Ia",
    strictness: "strict",
    scope: "ending",
    stem_final_match_present: "True",
    stem_final_match_imperfective: "False",
    stem_final_match_perfective: "True",
    stem_final_match_imperative: "True",
    stem_final_match_infinitive: "True",
  },
];

const mockClassPattern = {
  class: "Ia",
  "stem final": "k",
  present: "k",
  imperfective: "k",
  perfective: "k",
  imperative: "k",
  infinitive: "k",
};

describe("MatchExplorer", () => {
  it("renders a list of matches", () => {
    render(
      <MatchExplorer matches={mockMatches} classPattern={mockClassPattern} />
    );
    expect(screen.getByText("Verbs (2)")).toBeInTheDocument();
    expect(screen.getAllByText("test verb 1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("test verb 2").length).toBeGreaterThan(0);
  });

  it("displays details for the selected match", () => {
    render(
      <MatchExplorer matches={mockMatches} classPattern={mockClassPattern} />
    );

    // First verb should be selected by default
    expect(screen.getAllByText("test verb 1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Full Match").length).toBeGreaterThan(0);
  });

  it("updates details when a different verb is clicked", () => {
    render(
      <MatchExplorer matches={mockMatches} classPattern={mockClassPattern} />
    );

    const verb2 = screen.getByText("test verb 2");
    fireEvent.click(verb2);

    expect(screen.getAllByText("test verb 2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Near Miss").length).toBeGreaterThan(0);
  });
});
