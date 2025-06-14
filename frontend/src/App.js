import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      return true;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component
const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await login(credentials.username, credentials.password);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Sales CRM System</h1>
          <p className="text-gray-600 mt-2">Sign in to your account</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 font-medium">Demo Credentials:</p>
          <p className="text-xs text-gray-500 mt-1">Super Admin: tharme.ritta / Tharme@789</p>
        </div>
      </div>
    </div>
  );
};

// Super Admin Dashboard
const SuperAdminDashboard = () => {
  const [admins, setAdmins] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAdmin, setNewAdmin] = useState({ username: '', password: '', name: '' });
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    fetchAdmins();
  }, []);

  const fetchAdmins = async () => {
    try {
      const response = await axios.get(`${API}/super-admin/admins`);
      setAdmins(response.data);
    } catch (error) {
      console.error('Error fetching admins:', error);
    }
  };

  const createAdmin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/super-admin/admins`, {
        ...newAdmin,
        role: 'admin'
      });
      setNewAdmin({ username: '', password: '', name: '' });
      setShowCreateForm(false);
      fetchAdmins();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating admin');
    } finally {
      setLoading(false);
    }
  };

  const deleteAdmin = async (adminId) => {
    if (window.confirm('Are you sure you want to delete this admin?')) {
      try {
        await axios.delete(`${API}/super-admin/admins/${adminId}`);
        fetchAdmins();
      } catch (error) {
        alert(error.response?.data?.detail || 'Error deleting admin');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Super Admin Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, Super Admin</span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">Admin Management</h2>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                >
                  Create New Admin
                </button>
              </div>
            </div>

            <div className="p-6">
              {admins.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No admins created yet</p>
              ) : (
                <div className="space-y-4">
                  {admins.map((admin) => (
                    <div key={admin.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div>
                        <h3 className="font-medium text-gray-900">{admin.name || admin.username}</h3>
                        <p className="text-sm text-gray-500">Username: {admin.username}</p>
                        <p className="text-sm text-gray-500">Created: {new Date(admin.created_at).toLocaleDateString()}</p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => deleteAdmin(admin.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Admin Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Admin</h3>
            <form onSubmit={createAdmin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={newAdmin.username}
                  onChange={(e) => setNewAdmin({...newAdmin, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={newAdmin.password}
                  onChange={(e) => setNewAdmin({...newAdmin, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newAdmin.name}
                  onChange={(e) => setNewAdmin({...newAdmin, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Admin'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Admin Dashboard
const AdminDashboard = () => {
  const [agents, setAgents] = useState([]);
  const [saleRequests, setSaleRequests] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAgent, setNewAgent] = useState({ username: '', password: '', name: '' });
  const [activeTab, setActiveTab] = useState('agents');
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    fetchAgents();
    fetchSaleRequests();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/admin/agents`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchSaleRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/sale-requests`);
      setSaleRequests(response.data);
    } catch (error) {
      console.error('Error fetching sale requests:', error);
    }
  };

  const createAgent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/admin/agents`, {
        ...newAgent,
        role: 'agent'
      });
      setNewAgent({ username: '', password: '', name: '' });
      setShowCreateForm(false);
      fetchAgents();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating agent');
    } finally {
      setLoading(false);
    }
  };

  const approveSaleRequest = async (requestId) => {
    try {
      await axios.put(`${API}/admin/sale-requests/${requestId}/approve`);
      fetchSaleRequests();
      fetchAgents();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error approving sale request');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Admin Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, Admin</span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Tab Navigation */}
          <div className="mb-6">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('agents')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'agents'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Agents ({agents.length})
              </button>
              <button
                onClick={() => setActiveTab('requests')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'requests'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Sale Requests ({saleRequests.length})
              </button>
            </nav>
          </div>

          {/* Agents Tab */}
          {activeTab === 'agents' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Agent Management</h2>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    Create New Agent
                  </button>
                </div>
              </div>

              <div className="p-6">
                {agents.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No agents created yet</p>
                ) : (
                  <div className="space-y-4">
                    {agents.map((agent) => (
                      <div key={agent.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">{agent.name || agent.username}</h3>
                          <p className="text-sm text-gray-500">Username: {agent.username}</p>
                          <p className="text-sm text-gray-500">Coins: {agent.coins || 0} | Deposits: {agent.deposits || 0}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Sale Requests Tab */}
          {activeTab === 'requests' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Pending Sale Requests</h2>
              </div>

              <div className="p-6">
                {saleRequests.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No pending sale requests</p>
                ) : (
                  <div className="space-y-4">
                    {saleRequests.map((request) => (
                      <div key={request.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">Sale Amount: ${request.sale_amount}</h3>
                          <p className="text-sm text-gray-500">Agent ID: {request.agent_id}</p>
                          <p className="text-sm text-gray-500">Coins: {request.coins_requested} | Deposits: {request.deposits_requested}</p>
                          <p className="text-sm text-gray-500">Requested: {new Date(request.created_at).toLocaleString()}</p>
                        </div>
                        <button
                          onClick={() => approveSaleRequest(request.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                        >
                          Approve
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Agent Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Agent</h3>
            <form onSubmit={createAgent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={newAgent.username}
                  onChange={(e) => setNewAgent({...newAgent, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={newAgent.password}
                  onChange={(e) => setNewAgent({...newAgent, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Agent Dashboard
const AgentDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [prizes, setPrizes] = useState([]);
  const [rewardBag, setRewardBag] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSale, setSelectedSale] = useState('');
  const [loading, setLoading] = useState(false);
  const { logout, user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
    fetchPrizes();
    fetchRewardBag();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/agent/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchPrizes = async () => {
    try {
      const response = await axios.get(`${API}/shop/prizes`);
      setPrizes(response.data);
    } catch (error) {
      console.error('Error fetching prizes:', error);
    }
  };

  const fetchRewardBag = async () => {
    try {
      const response = await axios.get(`${API}/agent/reward-bag`);
      setRewardBag(response.data);
    } catch (error) {
      console.error('Error fetching reward bag:', error);
    }
  };

  const submitSaleRequest = async () => {
    if (!selectedSale) {
      alert('Please select a sale amount');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/agent/sale-request`, {
        sale_amount: selectedSale
      });
      setSelectedSale('');
      fetchDashboardData();
      alert('Sale request submitted successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error submitting sale request');
    } finally {
      setLoading(false);
    }
  };

  const redeemPrize = async (prizeId) => {
    try {
      await axios.post(`${API}/shop/redeem`, { prize_id: prizeId });
      fetchDashboardData();
      fetchPrizes();
      fetchRewardBag();
      alert('Prize redeemed successfully!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error redeeming prize');
    }
  };

  if (!dashboardData) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Agent Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.name || user?.username}</span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Tab Navigation */}
          <div className="mb-6">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'dashboard'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('shop')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'shop'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Shop
              </button>
              <button
                onClick={() => setActiveTab('rewards')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'rewards'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Reward Bag ({rewardBag.length})
              </button>
            </nav>
          </div>

          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">C</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Available Coins</dt>
                          <dd className="text-lg font-medium text-gray-900">{dashboardData.agent_info.coins}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">D</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Deposits</dt>
                          <dd className="text-lg font-medium text-gray-900">{dashboardData.agent_info.deposits}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">S</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Sales</dt>
                          <dd className="text-lg font-medium text-gray-900">${dashboardData.agent_info.total_sales}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold">P</span>
                        </div>
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Pending Requests</dt>
                          <dd className="text-lg font-medium text-gray-900">{dashboardData.pending_requests}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sale Request Form */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-medium text-gray-900">Submit Sale Request</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select Sale Amount
                      </label>
                      <select
                        value={selectedSale}
                        onChange={(e) => setSelectedSale(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Choose sale amount...</option>
                        <option value="100">$100 (0.5 coins, 1 deposit)</option>
                        <option value="250">$250 (1 coin, 1.5 deposits)</option>
                        <option value="500">$500 (3 coins, 3 deposits)</option>
                      </select>
                    </div>
                    <button
                      onClick={submitSaleRequest}
                      disabled={loading || !selectedSale}
                      className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium"
                    >
                      {loading ? 'Submitting...' : 'Submit Sale Request'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Shop Tab */}
          {activeTab === 'shop' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Prize Shop</h2>
                <p className="text-sm text-gray-500">Available Coins: {dashboardData.agent_info.coins}</p>
              </div>
              <div className="p-6">
                {prizes.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No prizes available</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {prizes.map((prize) => (
                      <div key={prize.id} className="border border-gray-200 rounded-lg p-4">
                        <h3 className="font-medium text-gray-900">{prize.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{prize.description}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <span className="text-lg font-bold text-blue-600">{prize.coin_cost} coins</span>
                          <button
                            onClick={() => redeemPrize(prize.id)}
                            disabled={dashboardData.agent_info.coins < prize.coin_cost}
                            className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1 rounded text-sm"
                          >
                            Redeem
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Reward Bag Tab */}
          {activeTab === 'rewards' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">My Reward Bag</h2>
              </div>
              <div className="p-6">
                {rewardBag.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No rewards in your bag</p>
                ) : (
                  <div className="space-y-4">
                    {rewardBag.map((reward) => (
                      <div key={reward.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">{reward.prize_name}</h3>
                          <p className="text-sm text-gray-500">Status: {reward.status}</p>
                          <p className="text-sm text-gray-500">Redeemed: {new Date(reward.redeemed_at).toLocaleDateString()}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            reward.status === 'unused' ? 'bg-green-100 text-green-800' :
                            reward.status === 'pending_use' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {reward.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  switch (user.role) {
    case 'super_admin':
      return <SuperAdminDashboard />;
    case 'admin':
      return <AdminDashboard />;
    case 'agent':
      return <AgentDashboard />;
    default:
      return <Login />;
  }
}

// Wrap the App with AuthProvider
export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}
