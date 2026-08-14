import type { Metadata } from "next";
import "./page.css";
import GameEmbed from "./GameEmbed";

export const metadata: Metadata = {
  title: "Cat's Emblem",
  description: "Play Cat's Emblem in your browser",
};

export default function CatsEmblemPage() {
  return (
    <div className="catsemblem-page">
      <GameEmbed />
    </div>
  );
}
