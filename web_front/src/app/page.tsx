import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-basketball-dark">
      <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">Basketball Stats</h1>
          <p className="text-xl opacity-90">Advanced basketball video analysis and statistics</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Public Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 text-basketball-orange">Public Stats</h2>
            <p className="text-gray-300 mb-6">
              Browse public basketball statistics, player profiles, and match results.
            </p>
            <div className="space-y-3">
              <Link href="/players" className="block btn-secondary text-center">
                View Players
              </Link>
              <Link href="/matches" className="block btn-secondary text-center">
                View Matches
              </Link>
            </div>
          </div>

          {/* Club Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 text-basketball-orange">Club Dashboard</h2>
            <p className="text-gray-300 mb-6">
              Access your private club dashboard for advanced analytics and video uploads.
            </p>
            <div className="space-y-3">
              <Link href="/club/login" className="block btn-primary text-center">
                Club Login
              </Link>
              <Link href="/club/dashboard" className="block btn-secondary text-center">
                Dashboard
              </Link>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="bg-basketball-orange w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Real-time Stats</h3>
            <p className="text-gray-400">Track player performance, distance covered, and ball possession in real-time.</p>
          </div>
          
          <div className="text-center">
            <div className="bg-basketball-orange w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🎥</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Video Analysis</h3>
            <p className="text-gray-400">Upload videos for automatic player tracking and shot detection.</p>
          </div>
          
          <div className="text-center">
            <div className="bg-basketball-orange w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🏀</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Advanced Metrics</h3>
            <p className="text-gray-400">Speed, distance, ball touches, and zone-based performance analysis.</p>
          </div>
        </div>
      </main>
    </div>
  )
}