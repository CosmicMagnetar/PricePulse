import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { signOut } from '../firebase';

const Navbar: React.FC = () => {
  const { user } = useAuth();

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              PricePulse
            </span>
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <div className="flex items-center space-x-2">
                  {user.photoURL && (
                    <img
                      src={user.photoURL}
                      alt={user.displayName || 'User'}
                      className="h-8 w-8 rounded-full"
                    />
                  )}
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {user.displayName || user.email}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Sign out
                </button>
              </>
            ) : (
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Please sign in
              </span>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 