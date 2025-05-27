import { useState, useEffect } from 'react'
import axios from 'axios'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import { collection, addDoc, serverTimestamp } from 'firebase/firestore'
import { db } from '../config/firebase'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const API_URL = 'https://pricepulse-avur.onrender.com'

interface PriceComparison {
  flipkart?: { price: number; url: string };
  meesho?: { price: number; url: string };
  ebay?: { price: number; url: string };
}

function Home() {
  const [url, setUrl] = useState('')
  const [product, setProduct] = useState<any>(null)
  const [priceHistory, setPriceHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [darkMode, setDarkMode] = useState(false)
  const [showAlertForm, setShowAlertForm] = useState(false)
  const [alertEmail, setAlertEmail] = useState('')
  const [targetPrice, setTargetPrice] = useState('')
  const [alertLoading, setAlertLoading] = useState(false)
  const [alertError, setAlertError] = useState('')
  const [alertSuccess, setAlertSuccess] = useState('')
  const [priceComparison, setPriceComparison] = useState<PriceComparison | null>(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // Check system preference for dark mode
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setDarkMode(true)
    }
  }, [])

  useEffect(() => {
    // Update document class for dark mode
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setPriceComparison(null)
    
    try {
      const response = await axios.post(`${API_URL}/track`, { url: url })
      setProduct(response.data.product)
      setPriceHistory(response.data.price_history)
      
      // Store search history in Firestore
      if (currentUser && response.data.product) {
        await addDoc(collection(db, 'searchHistory'), {
          userId: currentUser.uid,
          url: url,
          productName: response.data.product.name,
          price: response.data.product.current_price,
          imageUrl: response.data.product.image_url,
          timestamp: serverTimestamp()
        });
      }
      
      // Fetch price comparison
      if (response.data.product.id) {
        try {
          const comparisonResponse = await axios.get(`${API_URL}/compare/${response.data.product.id}`)
          setPriceComparison(comparisonResponse.data)
        } catch (comparisonErr) {
          console.error('Failed to fetch price comparison:', comparisonErr)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch product information')
    } finally {
      setLoading(false)
    }
  }

  const handleAlertSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setAlertLoading(true)
    setAlertError('')
    setAlertSuccess('')

    try {
      await axios.post(`${API_URL}/alerts`, {
        url: url,
        email: alertEmail,
        target_price: parseFloat(targetPrice)
      })
      setAlertSuccess('Price alert set successfully!')
      setShowAlertForm(false)
      setAlertEmail('')
      setTargetPrice('')
    } catch (err) {
      setAlertError('Failed to set price alert')
      console.error(err)
    } finally {
      setAlertLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Failed to log out:', error)
    }
  }

  const chartData = {
    labels: priceHistory.map(h => new Date(h.timestamp).toLocaleDateString()),
    datasets: [
      {
        label: 'Price History',
        data: priceHistory.map(h => h.price),
        borderColor: darkMode ? 'rgb(147, 197, 253)' : 'rgb(59, 130, 246)',
        tension: 0.1
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: darkMode ? 'white' : 'black'
        }
      }
    },
    scales: {
      y: {
        ticks: {
          color: darkMode ? 'white' : 'black'
        },
        grid: {
          color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
        }
      },
      x: {
        ticks: {
          color: darkMode ? 'white' : 'black'
        },
        grid: {
          color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
        }
      }
    }
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gray-100'} transition-colors duration-200`}>
      <div className="flex flex-col lg:flex-row min-h-screen">
        <div className={`w-full lg:w-1/3 p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
          <div className="max-w-md mx-auto">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              Price<span className="text-blue-500">Pulse</span>
            </h1>
            <div className="flex items-center space-x-3">
              <Link
                to="/profile"
                className="text-base font-medium text-gray-700 dark:text-gray-300 hover:underline hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-1.5 rounded-md bg-red-500 text-white text-sm font-medium hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-400 transition-all"
              >
                Logout
              </button>
            </div>
          </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Paste product URL (Amazon, Flipkart, etc.)"
                className={`w-full px-4 py-2 rounded-lg shadow-sm border focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 text-sm placeholder:text-gray-400 ${
                  darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-black'
                }`}
              />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition disabled:opacity-50 flex items-center justify-center"
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5 mr-2 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.37 0 0 5.37 0 12h4z"></path>
                  </svg>
                ) : null}
                {loading ? 'Fetching...' : 'Track Price'}
              </button>
            </form>

            {error && (
              <div className="text-red-500 text-center mt-4">{error}</div>
            )}
          </div>
        </div>

        <div className="flex-1 p-6 lg:p-8 flex items-start justify-center overflow-y-auto" style={{ height: "100vh", width:"calc(100vw - 300px)" }}>
          <div className="w-full max-w-4xl pt-8">
            {product ? (
              <div className={`${darkMode ? 'text-white' : 'text-gray-900'}`}>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
                      <h2 className="text-xl font-semibold mb-4 line-clamp-2">{product.name}</h2>
                      {product.image_url && (
                        <div className="mb-4">
                          <img
                            src={product.image_url}
                            alt={product.name}
                            className="w-full h-64 object-contain"
                          />
                        </div>
                      )}
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-4">
                        Current Price: ₹{Number(product.current_price).toLocaleString('en-IN', {
                          maximumFractionDigits: 0,
                          minimumFractionDigits: 0
                        })}
                      </p>
                      
                      {/* Price Comparison Section */}
                      <div className="mt-6">
                        <h3 className="text-lg font-semibold mb-4">Price Comparison</h3>
                        {priceComparison ? (
                          <div className="space-y-4">
                            {priceComparison.flipkart && (
                              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                                <span className="font-medium">Flipkart</span>
                                <div className="text-right">
                                  <p className="text-lg font-semibold">₹{Number(priceComparison.flipkart.price).toLocaleString('en-IN', {
                                    maximumFractionDigits: 0,
                                    minimumFractionDigits: 0
                                  })}</p>
                                  <a
                                    href={priceComparison.flipkart.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-500 hover:text-blue-600"
                                  >
                                    View on Flipkart
                                  </a>
                                </div>
                              </div>
                            )}
                            {priceComparison.meesho && (
                              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                                <span className="font-medium">Meesho</span>
                                <div className="text-right">
                                  <p className="text-lg font-semibold">₹{Number(priceComparison.meesho.price).toLocaleString('en-IN', {
                                    maximumFractionDigits: 0,
                                    minimumFractionDigits: 0
                                  })}</p>
                                  <a
                                    href={priceComparison.meesho.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-500 hover:text-blue-600"
                                  >
                                    View on Meesho
                                  </a>
                                </div>
                              </div>
                            )}
                            {priceComparison.ebay && (
                              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                                <span className="font-medium">eBay</span>
                                <div className="text-right">
                                  <p className="text-lg font-semibold">₹{Number(priceComparison.ebay.price).toLocaleString('en-IN', {
                                    maximumFractionDigits: 0,
                                    minimumFractionDigits: 0
                                  })}</p>
                                  <a
                                    href={priceComparison.ebay.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-500 hover:text-blue-600"
                                  >
                                    View on eBay
                                  </a>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 dark:text-gray-400">No price comparison available</p>
                        )}
                      </div>

                      {/* Price Alert Form */}
                      <div className="mt-6">
                        <button
                          onClick={() => setShowAlertForm(!showAlertForm)}
                          className="w-full bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                        >
                          {showAlertForm ? 'Cancel Alert' : 'Set Price Alert'}
                        </button>

                        {showAlertForm && (
                          <form onSubmit={handleAlertSubmit} className="mt-4 space-y-4">
                            <div>
                              <input
                                type="email"
                                value={alertEmail}
                                onChange={(e) => setAlertEmail(e.target.value)}
                                placeholder="Enter your email"
                                className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                                  darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-black'
                                }`}
                                required
                              />
                            </div>
                            <div>
                              <input
                                type="number"
                                value={targetPrice}
                                onChange={(e) => setTargetPrice(e.target.value)}
                                placeholder="Enter target price"
                                className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                                  darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-black'
                                }`}
                                required
                              />
                            </div>
                            <button
                              type="submit"
                              disabled={alertLoading}
                              className="w-full bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {alertLoading ? 'Setting Alert...' : 'Set Alert'}
                            </button>
                            {alertError && (
                              <div className="text-red-500 text-center">{alertError}</div>
                            )}
                            {alertSuccess && (
                              <div className="text-green-500 text-center">{alertSuccess}</div>
                            )}
                          </form>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
                      <h3 className="text-xl font-semibold mb-4">Price History</h3>
                      <div className="h-80">
                        <Line data={chartData} options={chartOptions} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className={`text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                <p className="text-lg">Enter an Amazon product URL to start tracking prices</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home 