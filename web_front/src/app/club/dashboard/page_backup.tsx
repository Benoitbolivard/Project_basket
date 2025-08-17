"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthService } from "@/lib/auth";

type Player = { id: string; name: string; number: number | null };
type JobStatus = { status: string; result?: any };

interface PlayerStats {
  player_id: number
  player_name: string
  jersey_number?: number
  position?: string
  games_played: number
  total_minutes: number
  total_distance_m: number
  avg_speed_kmh: number
  total_ball_touches: number
  avg_touches_per_game: number
}

interface DashboardData {
  club: {
    id: number
    name: string
    code: string
    city?: string
  }
  players: PlayerStats[]
  summary: {
    total_players: number
    active_players: number
  }
}

export default function ClubDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    // Check authentication
    if (!AuthService.isAuthenticated()) {
      router.push('/club/login')
      return
    }

    // Check role
    const user = AuthService.getUser()
    if (!user || user.role !== 'club') {
      router.push('/')
      return
    }

    fetchDashboardData()
  }, [router])

  const fetchDashboardData = async () => {
    try {
      const data = await ApiClient.get('/club/dashboard-data')
      setDashboardData(data)
      setLoading(false)
    } catch (err) {
      if (err instanceof Error && err.message === 'Authentication required') {
        router.push('/club/login')
        return
      }
      setError('Failed to load dashboard data')
      setLoading(false)
    }
  }

  const handleLogout = () => {
    AuthService.logout()
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-basketball-dark flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-basketball-dark flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">{error}</div>
          <button onClick={fetchDashboardData} className="btn-primary">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-basketball-dark flex items-center justify-center">
        <div className="text-white text-xl">No data available</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-basketball-dark">
      <header className="bg-basketball-gray border-b border-gray-700 p-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              {dashboardData.club.name} Dashboard
            </h1>
            <p className="text-gray-400">
              {dashboardData.club.city && `${dashboardData.club.city} • `}
              {dashboardData.summary.active_players} active players
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-white font-medium">{AuthService.getUser()?.username}</div>
              <div className="text-gray-400 text-sm">Club Member</div>
            </div>
            <button onClick={handleLogout} className="btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="card text-center">
            <div className="text-3xl font-bold text-basketball-orange mb-2">
              {dashboardData.summary.total_players}
            </div>
            <div className="text-gray-300">Total Players</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-basketball-orange mb-2">
              {dashboardData.summary.active_players}
            </div>
            <div className="text-gray-300">Active Players</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-basketball-orange mb-2">
              {dashboardData.players.reduce((sum, p) => sum + p.games_played, 0)}
            </div>
            <div className="text-gray-300">Total Games</div>
          </div>
        </div>

        {/* Video Upload Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Upload Video for Analysis</h2>
          <VideoUpload />
        </div>

        {/* Player Stats Table */}
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-6">Player Statistics</h2>
          
          {dashboardData.players.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-4xl mb-4">📊</div>
              <p>No player statistics available yet.</p>
              <p className="text-sm mt-2">Upload and analyze some game videos to see player stats here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-600">
                    <th className="text-gray-300 font-semibold py-3 px-4">Player</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Position</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Games</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Minutes</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Distance (m)</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Avg Speed (km/h)</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Ball Touches</th>
                    <th className="text-gray-300 font-semibold py-3 px-4">Touches/Game</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.players.map((player) => (
                    <tr key={player.player_id} className="border-b border-gray-700 hover:bg-gray-800 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-center">
                          <div>
                            <div className="font-medium text-white">{player.player_name}</div>
                            {player.jersey_number && (
                              <div className="text-gray-400 text-sm">#{player.jersey_number}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-gray-300">{player.position || '-'}</td>
                      <td className="py-4 px-4 text-gray-300">{player.games_played}</td>
                      <td className="py-4 px-4 text-gray-300">{player.total_minutes.toFixed(1)}</td>
                      <td className="py-4 px-4 text-gray-300">{player.total_distance_m.toFixed(1)}</td>
                      <td className="py-4 px-4 text-gray-300">{player.avg_speed_kmh.toFixed(1)}</td>
                      <td className="py-4 px-4 text-gray-300">{player.total_ball_touches}</td>
                      <td className="py-4 px-4 text-gray-300">{player.avg_touches_per_game.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}