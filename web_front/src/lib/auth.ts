/**
 * Authentication utilities for JWT handling
 */

interface User {
  id: number
  username: string
  email: string
  role: string
  club_id?: number
}

interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class AuthService {
  private static TOKEN_KEY = 'basketball_auth_token'
  private static USER_KEY = 'basketball_user'

  static async login(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const authData: AuthResponse = await response.json()
    
    // Store token and user data
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.TOKEN_KEY, authData.access_token)
      localStorage.setItem(this.USER_KEY, JSON.stringify(authData.user))
    }

    return authData
  }

  static async register(
    username: string,
    email: string,
    password: string,
    role: string = 'public',
    clubId?: number
  ): Promise<any> {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        email,
        password,
        role,
        ...(clubId && { club_id: clubId.toString() }),
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    return response.json()
  }

  static logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.TOKEN_KEY)
      localStorage.removeItem(this.USER_KEY)
    }
  }

  static getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(this.TOKEN_KEY)
    }
    return null
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(this.USER_KEY)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static isAuthenticated(): boolean {
    return this.getToken() !== null
  }

  static hasRole(role: string): boolean {
    const user = this.getUser()
    return user?.role === role
  }

  static async getCurrentUser(): Promise<User> {
    const token = this.getToken()
    if (!token) {
      throw new Error('No authentication token')
    }

    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      this.logout() // Clear invalid token
      throw new Error('Authentication failed')
    }

    const user = await response.json()
    
    // Update stored user data
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user))
    }

    return user
  }

  static getAuthHeaders(): Record<string, string> {
    const token = this.getToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
  }
}

// API client with authentication
export class ApiClient {
  static async get(endpoint: string): Promise<any> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        ...AuthService.getAuthHeaders(),
      },
    })

    if (!response.ok) {
      if (response.status === 401) {
        AuthService.logout()
        throw new Error('Authentication required')
      }
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  static async post(endpoint: string, data: any): Promise<any> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...AuthService.getAuthHeaders(),
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      if (response.status === 401) {
        AuthService.logout()
        throw new Error('Authentication required')
      }
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }
}