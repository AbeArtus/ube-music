import type { Metadata } from "next";
import "./page.css";

export const metadata: Metadata = {
  title: "Cat's Emblem",
  description: "Play Cat's Emblem in your browser",
};

export default function CatsEmblemPage() {
  return (
    <div className="catsemblem-page">
      <iframe
        className="catsemblem-frame"
        src="/build/web/index.html"
        title="Cat's Emblem"
        allow="autoplay; fullscreen"
        allowFullScreen
      />
    </div>
  );
}
