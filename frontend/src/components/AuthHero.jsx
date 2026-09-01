import { Gavel, Scale, ShieldCheck } from 'lucide-react'

import GovernAILogo from './Logo.jsx'

/**
 * The left-hand marketing panel shared by the Login and Sign up screens.
 * Markup/classes are unchanged from the original login design.
 */
export default function AuthHero({ gradientId = 'auth-logo' }) {
  return (
    <div className="login-hero">
      <div className="login-hero-top">
        <GovernAILogo size={34} gradientId={gradientId} />
        <span className="login-hero-brand">
          Govern<span className="brand-ai">AI</span>
        </span>
      </div>

      <div className="login-hero-mid">
        <div className="login-hero-kicker">Multi-agent governance</div>
        <h1 className="login-hero-title">
          Every AI use case reviewed before it ships.
        </h1>
        <p className="login-hero-sub">
          Risk assessment, policy compliance and a decision — three agents,
          real tools, an append-only audit trail.
        </p>

        <div className="login-hero-pills">
          <span className="login-pill login-pill-teal">
            <ShieldCheck size={13} />
            Risk agent
          </span>
          <span className="login-pill login-pill-violet">
            <Scale size={13} />
            Policy agent
          </span>
          <span className="login-pill login-pill-neutral">
            <Gavel size={13} />
            Decision agent
          </span>
        </div>
      </div>

      <div className="login-hero-foot">
        POL-001 – POL-140 · audit_log.jsonl · OpenAI
      </div>
    </div>
  )
}
