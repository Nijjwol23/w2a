/**
 * W2A JavaScript/TypeScript SDK
 * Web2Agent Protocol client for Node.js, browsers, and edge runtimes.
 *
 * npm install w2a-client
 *
 * import { discover } from 'w2a-client'
 * const site = await discover('stripe.com')
 */

// ── Types ──────────────────────────────────────────────────────────────────

export interface W2ASkill {
  id: string
  intent: string
  action: string
  auth: 'none' | 'session' | 'bearer' | 'apikey' | 'oauth2'
  input: Record<string, string>
  output: Record<string, string>
  description?: string
  /** HTTP method extracted from action */
  readonly method: string
  /** URL path extracted from action */
  readonly path: string
  /** True if auth !== 'none' */
  readonly requiresAuth: boolean
}

export interface W2APolicy {
  rate_limit?: string
  allowed_agents: string[]
  blocked_agents: string[]
  require_identity: boolean
  /** True if all agents are allowed */
  readonly isOpen: boolean
}

export interface W2ASite {
  name: string
  type: string
  origin: string
  manifestUrl: string
  language: string
  description?: string
  skills: W2ASkill[]
  policy?: W2APolicy
  a2aCompatible: boolean
  w2aVersion: string
  /** Skills that require no authentication */
  readonly publicSkills: W2ASkill[]
  /** Look up a skill by id */
  getSkill(id: string): W2ASkill | undefined
  /** Find a skill by searching intent strings */
  findSkill(fragment: string): W2ASkill | undefined
}

export interface W2AClientOptions {
  /** Request timeout in ms (default: 10000) */
  timeout?: number
  /** Validate manifest against the W2A spec (adds a network round-trip) */
  validate?: boolean
  /** Additional headers to send with all requests */
  headers?: Record<string, string>
  /** Custom fetch implementation (defaults to global fetch) */
  fetch?: typeof fetch
}

export class W2AError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message)
    this.name = 'W2AError'
  }
}

export class ManifestNotFoundError extends W2AError {
  constructor(public readonly url: string) {
    super(
      `No W2A manifest at ${url}/.well-known/agents.json — ` +
      `this site hasn't adopted W2A yet. ` +
      `Generate one at https://w2a-protocol.org/tools`,
      'MANIFEST_NOT_FOUND'
    )
    this.name = 'ManifestNotFoundError'
  }
}

export class ManifestInvalidError extends W2AError {
  constructor(public readonly url: string, public readonly errors: any[]) {
    super(`W2A manifest at ${url} is invalid`, 'MANIFEST_INVALID')
    this.name = 'ManifestInvalidError'
  }
}

export class SkillNotFoundError extends W2AError {
  constructor(public readonly skillId: string, available: string[]) {
    super(
      `Skill '${skillId}' not found. Available: ${available.join(', ')}`,
      'SKILL_NOT_FOUND'
    )
    this.name = 'SkillNotFoundError'
  }
}

// ── Internal helpers ─────────────────────────────────────────────────────────

const W2A_HEADERS = {
  'Accept': 'application/json',
  'Agent-W2A': '1.0',
  'User-Agent': 'W2A-JS-SDK/0.1.0 (+https://w2a-protocol.org)',
}

function normaliseUrl(url: string): string {
  if (!url.startsWith('http')) url = 'https://' + url
  const parsed = new URL(url)
  return parsed.origin
}

function parseSkill(raw: any): W2ASkill {
  const action: string = raw.action || 'GET /'
  const parts = action.split(' ')
  return {
    id: raw.id || '',
    intent: raw.intent || '',
    action,
    auth: raw.auth || 'none',
    input: raw.input || {},
    output: raw.output || {},
    description: raw.description,
    get method() { return parts[0]?.toUpperCase() || 'GET' },
    get path() { return parts[1] || '/' },
    get requiresAuth() { return this.auth !== 'none' },
  }
}

function parseSite(origin: string, manifest: any): W2ASite {
  const siteData = manifest.site || {}
  const skillsRaw: any[] = manifest.skills || manifest.capabilities || []
  const policyRaw = manifest.policies || {}

  const skills = skillsRaw.map(parseSkill)

  const policy: W2APolicy = {
    rate_limit: policyRaw.rate_limit,
    allowed_agents: policyRaw.allowed_agents || ['*'],
    blocked_agents: policyRaw.blocked_agents || [],
    require_identity: policyRaw.require_identity || false,
    get isOpen() { return this.allowed_agents.includes('*') },
  }

  const site: W2ASite = {
    name: siteData.name || origin,
    type: siteData.type || 'other',
    origin,
    manifestUrl: `${origin}/.well-known/agents.json`,
    language: siteData.language || 'en',
    description: siteData.description,
    skills,
    policy,
    a2aCompatible: Boolean(manifest.a2a_profile),
    w2aVersion: manifest.w2a || '1.0',
    get publicSkills() { return this.skills.filter(s => s.auth === 'none') },
    getSkill(id: string) { return this.skills.find(s => s.id === id) },
    findSkill(fragment: string) {
      const f = fragment.toLowerCase()
      return this.skills.find(
        s => s.id.toLowerCase().includes(f) || s.intent.toLowerCase().includes(f)
      )
    },
  }

  return site
}

// ── W2AClient ─────────────────────────────────────────────────────────────────

export class W2AClient {
  private opts: Required<W2AClientOptions>

  constructor(options: W2AClientOptions = {}) {
    this.opts = {
      timeout: options.timeout ?? 10_000,
      validate: options.validate ?? false,
      headers: options.headers ?? {},
      fetch: options.fetch ?? globalThis.fetch,
    }
  }

  /**
   * Discover a W2A-enabled site and return its capabilities.
   *
   * @param url - Site URL or domain. e.g. "stripe.com"
   * @throws {ManifestNotFoundError} if the site has no agents.json
   * @throws {ManifestInvalidError} if validate:true and manifest is invalid
   *
   * @example
   * const client = new W2AClient()
   * const site = await client.discover('w2a-protocol.org')
   * console.log(site.skills.map(s => s.intent))
   */
  async discover(url: string): Promise<W2ASite> {
    const origin = normaliseUrl(url)
    const manifestUrl = `${origin}/.well-known/agents.json`

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.opts.timeout)

    let manifest: any
    try {
      const res = await this.opts.fetch(manifestUrl, {
        headers: { ...W2A_HEADERS, ...this.opts.headers },
        signal: controller.signal,
      })

      clearTimeout(timer)

      if (res.status === 404 || !res.ok) {
        throw new ManifestNotFoundError(origin)
      }

      manifest = await res.json()
    } catch (err: any) {
      clearTimeout(timer)
      if (err instanceof ManifestNotFoundError) throw err
      throw new ManifestNotFoundError(origin)
    }

    if (this.opts.validate) {
      await this._validate(manifest, origin)
    }

    return parseSite(origin, manifest)
  }

  /**
   * Call a skill on a W2A-enabled site.
   *
   * @param site - W2ASite returned by discover()
   * @param skillId - The skill id to invoke
   * @param params - Parameters matching the skill's input schema
   * @param headers - Optional additional headers (e.g. auth tokens)
   *
   * @example
   * const result = await client.call(site, 'search_products', { q: 'shoes' })
   */
  async call(
    site: W2ASite,
    skillId: string,
    params: Record<string, any> = {},
    headers: Record<string, string> = {}
  ): Promise<any> {
    const skill = site.getSkill(skillId)
    if (!skill) {
      throw new SkillNotFoundError(skillId, site.skills.map(s => s.id))
    }

    // Resolve path parameters (:id, :slug etc.)
    let resolvedPath = skill.path
    const remainingParams = { ...params }
    resolvedPath = resolvedPath.replace(/:([a-zA-Z_]+)/g, (_, name) => {
      if (remainingParams[name] !== undefined) {
        const val = remainingParams[name]
        delete remainingParams[name]
        return encodeURIComponent(String(val))
      }
      return `:${name}`
    })

    let url = `${site.origin}${resolvedPath}`
    const reqHeaders: Record<string, string> = {
      ...W2A_HEADERS,
      ...this.opts.headers,
      ...headers,
    }

    const init: RequestInit = { method: skill.method, headers: reqHeaders }

    if (skill.method === 'GET' || skill.method === 'DELETE') {
      const qs = new URLSearchParams()
      for (const [k, v] of Object.entries(remainingParams)) {
        if (v !== undefined && v !== null) qs.set(k, String(v))
      }
      const qStr = qs.toString()
      if (qStr) url += `?${qStr}`
    } else {
      reqHeaders['Content-Type'] = 'application/json'
      init.body = JSON.stringify(remainingParams)
    }

    const res = await this.opts.fetch(url, init)
    return res.json()
  }

  private async _validate(manifest: any, origin: string): Promise<void> {
    try {
      const res = await this.opts.fetch('https://w2a-protocol.org/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manifest }),
      })
      if (res.ok) {
        const data = await res.json()
        if (!data.valid) {
          throw new ManifestInvalidError(origin, data.errors || [])
        }
      }
    } catch (err) {
      if (err instanceof ManifestInvalidError) throw err
      // Validator unavailable — don't block discovery
    }
  }
}

// ── Module-level shortcuts ────────────────────────────────────────────────────

/**
 * Discover a W2A-enabled site. The main entry point for most use cases.
 *
 * @example
 * import { discover } from 'w2a-client'
 *
 * const site = await discover('w2a-protocol.org')
 * console.log(`${site.name} has ${site.skills.length} skills`)
 *
 * for (const skill of site.publicSkills) {
 *   console.log(`${skill.id}: ${skill.intent}`)
 * }
 */
export async function discover(
  url: string,
  options: W2AClientOptions = {}
): Promise<W2ASite> {
  return new W2AClient(options).discover(url)
}

/**
 * Check if a site has a valid W2A manifest without fetching full details.
 * Useful for quick presence checks.
 *
 * @example
 * if (await isEnabled('stripe.com')) {
 *   const site = await discover('stripe.com')
 * }
 */
export async function isEnabled(
  url: string,
  options: W2AClientOptions = {}
): Promise<boolean> {
  try {
    await new W2AClient(options).discover(url)
    return true
  } catch {
    return false
  }
}
