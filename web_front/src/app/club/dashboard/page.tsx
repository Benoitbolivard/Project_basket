'use client'

import { useState, useEffect } from 'react'
import VideoUpload from '@/components/VideoUpload'

interface PlayerStats {
  player_id: number
  player_name: string
  minutes_played: number
  distance_covered_m: number
  avg_speed_kmh: number
  ball_touches: number
  games_played: number
}

export default function ClubDashboard() {
  const [players, setPlayers] = useState<PlayerStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlayers()
  }, [])

  const fetchPlayers = async () => {
    try {
      // This would be replaced with actual API call to get club players
      // For now, we'll use mock data
      setPlayers([
        {
          player_id: 1,
          player_name: "LeBron James",
          minutes_played: 145.5,
          distance_covered_m: 2840.5,
          avg_speed_kmh: 12.8,
          ball_touches: 89,
          games_played: 5
        },
        {
          player_id: 2,
          player_name: "Stephen Curry",
          minutes_played: 138.2,
          distance_covered_m: 2650.3,
          avg_speed_kmh: 11.9,
          ball_touches: 156,
          games_played: 5
        },
        {
          player_id: 3,
          player_name: "Kevin Durant",
          minutes_played: 142.8,
          distance_covered_m: 2720.1,
          avg_speed_kmh: 12.1,
          ball_touches: 124,
          games_played: 5
        }
      ])
      setLoading(false)
    } catch (err) {
      setError('Failed to load players')
      setLoading(false)
    }
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
        <div className="text-red-500 text-xl">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-basketball-dark">
      <header className="bg-basketball-gray border-b border-gray-700 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-2">Club Dashboard</h1>
          <p className="text-gray-400">Manage your team's analytics and video uploads</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Video Upload Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Upload Video for Analysis</h2>
          <VideoUpload />
        </div>

        {/* Player Stats Table */}
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-6">Player Statistics</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-600">
                  <th className="text-gray-300 font-semibold py-3 px-4">Player</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Games</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Minutes</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Distance (m)</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Avg Speed (km/h)</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Ball Touches</th>
                  <th className="text-gray-300 font-semibold py-3 px-4">Touches/Game</th>
                </tr>
              </thead>
              <tbody>
                {players.map((player) => (
                  <tr key={player.player_id} className="border-b border-gray-700 hover:bg-gray-800 transition-colors">
                    <td className="py-4 px-4">
                      <div className="font-medium text-white">{player.player_name}</div>
                    </td>
                    <td className="py-4 px-4 text-gray-300">{player.games_played}</td>
                    <td className="py-4 px-4 text-gray-300">{player.minutes_played.toFixed(1)}</td>
                    <td className="py-4 px-4 text-gray-300">{player.distance_covered_m.toFixed(1)}</td>
                    <td className="py-4 px-4 text-gray-300">{player.avg_speed_kmh.toFixed(1)}</td>
                    <td className="py-4 px-4 text-gray-300">{player.ball_touches}</td>
                    <td className="py-4 px-4 text-gray-300">
                      {(player.ball_touches / player.games_played).toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}