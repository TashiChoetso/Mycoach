import Link from "next/link";
import { CalmHorizon } from "@/components/CalmHorizon";

export default function HomePage() {
  return (
    <CalmHorizon>
      <p className="wordmark calm-wordmark">MyCoach</p>
      <div className="ikigai-card">
        <p className="ikigai-kicker">IKIGAI / 生き甲斐</p>
        <h1>Discover your reason for being.</h1>
        <p>A quiet room for the life you want to tend. There is no hurry here.</p>
      </div>
      <div className="row calm-actions">
        <Link className="btn" href="/signup">
          Begin
        </Link>
        <Link className="btn secondary" href="/login">
          I already have a room
        </Link>
      </div>
    </CalmHorizon>
  );
}
