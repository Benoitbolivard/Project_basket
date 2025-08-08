'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

interface Match {
  match_id: number
  match_date: string
  home_team: any
  away_team: any
  final_score?: {
    home: number
    away: number
  }
  duration_minutes?: number
  status: string
}

export default function MatchPage() {
  const searchParams = useSearchParams()
  const matchId = searchParams.get('id')
  
  const [match, setMatch] = useState<Match | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (matchId) {
      fetchMatchData(parseInt(matchId))
    }
  }, [matchId])

  const fetchMatchData = async (id: number) => {
    try {
      // For now using mock data - replace with actual API call
      const mockMatch: Match = {
        match_id: id,
        match_date: '2024-01-15T19:30:00',
        home_team: {
          team_name: 'Lakers',
          total_points: 108,
          field_goal_percentage: 47.2,
          three_point_percentage: 35.8,
          total_distance_covered_m: 12840.5,
          players: [
            { name: 'LeBron James', points: 28, distance_covered_m: 2840.5 },
            { name: 'Anthony Davis', points: 24, distance_covered_m: 2650.3 },
          ]
        },
        away_team: {
          team_name: 'Warriors',
          total_points: 112,
          field_goal_percentage: 49.1,
          three_point_percentage: 42.3,
          total_distance_covered_m: 13120.8,
          players: [
            { name: 'Stephen Curry', points: 32, distance_covered_m: 2720.1 },
            { name: 'Klay Thompson', points: 22, distance_covered_m: 2590.7 },
          ]
        },
        final_score: { home: 108, away: 112 },
        duration_minutes: 48,
        status: 'finished'
      }
      
      setMatch(mockMatch)
      setLoading(false)
    } catch (err) {
      setError('Failed to load match data')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-basketball-dark flex items-center justify-center">
        <div className="text-white text-xl">Loading match data...</div>
      </div>
    )
  }

  if (error || !match) {
    return (
      <div className="min-h-screen bg-basketball-dark flex items-center justify-center">
        <div className="text-red-500 text-xl">{error || 'Match not found'}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-basketball-dark">
      <header className="bg-basketball-gray border-b border-gray-700 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-2">Match Statistics</h1>
          <p className="text-gray-400">{new Date(match.match_date).toLocaleDateString()} - {match.status}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Score Card */}
        <div className="card mb-8">
          <div className="flex justify-between items-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white">{match.home_team.team_name}</h2>
              <div className="text-4xl font-bold text-basketball-orange mt-2">
                {match.final_score?.home || 0}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-gray-400 text-lg">VS</div>
              <div className="text-sm text-gray-500 mt-2">
                {match.duration_minutes} min
              </div>
            </div>
            
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white">{match.away_team.team_name}</h2>
              <div className="text-4xl font-bold text-basketball-orange mt-2">
                {match.final_score?.away || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Team Stats Comparison */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Home Team */}
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">{match.home_team.team_name} Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-300">Field Goal %</span>
                <span className="text-white font-medium">{match.home_team.field_goal_percentage}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">3-Point %</span>
                <span className="text-white font-medium">{match.home_team.three_point_percentage}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Total Distance</span>
                <span className="text-white font-medium">{match.home_team.total_distance_covered_m.toFixed(0)}m</span>
              </div>
            </div>
          </div>

          {/* Away Team */}
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">{match.away_team.team_name} Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-300">Field Goal %</span>
                <span className="text-white font-medium">{match.away_team.field_goal_percentage}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">3-Point %</span>
                <span className="text-white font-medium">{match.away_team.three_point_percentage}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Total Distance</span>
                <span className="text-white font-medium">{match.away_team.total_distance_covered_m.toFixed(0)}m</span>
              </div>
            </div>
          </div>
        </div>

        {/* Player Stats */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-white mb-4">Player Performance</h3>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Home Team Players */}
            <div>
              <h4 className="text-lg font-semibold text-basketball-orange mb-3">{match.home_team.team_name}</h4>
              <div className="space-y-2">
                {match.home_team.players.map((player: any, index: number) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b border-gray-700">
                    <span className="text-white">{player.name}</span>
                    <div className="text-right">
                      <div className="text-white font-medium">{player.points} pts</div>
                      <div className="text-gray-400 text-sm">{player.distance_covered_m.toFixed(0)}m</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Away Team Players */}
            <div>
              <h4 className="text-lg font-semibold text-basketball-orange mb-3">{match.away_team.team_name}</h4>
              <div className="space-y-2">
                {match.away_team.players.map((player: any, index: number) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b border-gray-700">
                    <span className="text-white">{player.name}</span>
                    <div className="text-right">
                      <div className="text-white font-medium">{player.points} pts</div>
                      <div className="text-gray-400 text-sm">{player.distance_covered_m.toFixed(0)}m</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Heat Map Placeholder */}
        <div className="card">
          <h3 className="text-xl font-bold text-white mb-4">Court Heat Map</h3>
          <div className="bg-green-900 rounded-lg p-8 text-center">
            <div className="text-6xl mb-4">🏀</div>
            <p className="text-gray-300 text-lg">Heat Map Visualization</p>
            <p className="text-gray-500 mt-2">Player movement and shot locations will be displayed here</p>
            <div className="mt-6 bg-green-800 rounded p-4 max-w-md mx-auto">
              <p className="text-green-200 text-sm">
                📍 Shot locations<br/>
                🔥 High activity zones<br/>
                📊 Movement patterns
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}