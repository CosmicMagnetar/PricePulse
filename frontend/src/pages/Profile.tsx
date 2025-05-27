import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { db } from '../config/firebase';
import { collection, query, where, orderBy, getDocs } from 'firebase/firestore';
import { Link } from 'react-router-dom';

interface PriceComparisonData {
  price: number;
  url: string;
}

interface SearchHistory {
  id: string;
  url: string;
  timestamp: Date;
  productName: string;
  price: number;
  imageUrl: string;
  priceComparison?: {
    flipkart?: PriceComparisonData;
    meesho?: PriceComparisonData;
    ebay?: PriceComparisonData;
  };
}

export default function Profile() {
  const { currentUser } = useAuth();
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSearchHistory() {
      if (!currentUser) return;

      try {
        const searchHistoryRef = collection(db, 'searchHistory');
        const q = query(
          searchHistoryRef,
          where('userId', '==', currentUser.uid),
          orderBy('timestamp', 'desc')
        );

        const querySnapshot = await getDocs(q);
        const history = querySnapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data(),
          timestamp: doc.data().timestamp.toDate()
        })) as SearchHistory[];

        setSearchHistory(history);
      } catch (error) {
        console.error('Error fetching search history:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchSearchHistory();
  }, [currentUser]);

  if (!currentUser) {
    return <div className="text-center mt-20 text-lg text-gray-600 dark:text-gray-300">Please log in to view your profile.</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Profile Info Card */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Profile</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
              <p className="mt-1 text-lg text-gray-900 dark:text-white">{currentUser.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Account Created</label>
              <p className="mt-1 text-lg text-gray-900 dark:text-white">
                {currentUser.metadata.creationTime
                  ? new Date(currentUser.metadata.creationTime).toLocaleDateString()
                  : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Search History Section */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Search History</h2>
            <Link
              to="/"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm"
            >
              Back to Home
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading...</div>
          ) : searchHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">No search history found</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchHistory.map((item) => (
                <div
                  key={item.id}
                  className="bg-gray-50 dark:bg-gray-700 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200"
                >
                  {item.imageUrl && (
                    <img
                      src={item.imageUrl}
                      alt={item.productName}
                      className="w-full h-48 object-contain bg-white"
                    />
                  )}
                  <div className="p-4 space-y-2">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white line-clamp-2">
                      {item.productName}
                    </h3>
                    <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                      ₹{item.price.toLocaleString('en-IN', {
                        maximumFractionDigits: 0,
                        minimumFractionDigits: 0
                      })}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {item.timestamp.toLocaleString()}
                    </p>

                    {item.priceComparison && (
                      <div className="pt-4 border-t border-gray-200 dark:border-gray-600 space-y-1">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Comparisons:</h4>
                        {Object.entries(item.priceComparison).map(([platform, data]) =>
                          data ? (
                            <div key={platform} className="flex justify-between text-sm">
                              <span className="text-gray-700 dark:text-gray-300 capitalize">{platform}:</span>
                              <a
                                href={data.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 dark:text-blue-400 hover:underline"
                              >
                                ₹{data.price.toLocaleString('en-IN', {
                                  maximumFractionDigits: 0,
                                  minimumFractionDigits: 0
                                })}
                              </a>
                            </div>
                          ) : null
                        )}
                      </div>
                    )}

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block text-sm mt-3 text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View Product on Amazon
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
