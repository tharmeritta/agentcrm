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
  const [agents, setAgents] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [prizes, setPrizes] = useState([]);
  const [coinRequests, setCoinRequests] = useState([]);
  const [showCreateAdminForm, setShowCreateAdminForm] = useState(false);
  const [showCreateAgentForm, setShowCreateAgentForm] = useState(false);
  const [showCreatePrizeForm, setShowCreatePrizeForm] = useState(false);
  const [showEditPrizeForm, setShowEditPrizeForm] = useState(false);
  const [showEditUserForm, setShowEditUserForm] = useState(false);
  const [newAdmin, setNewAdmin] = useState({ username: '', password: '', name: '' });
  const [newAgent, setNewAgent] = useState({ username: '', password: '', name: '' });
  const [newPrize, setNewPrize] = useState({ 
    name: '', 
    description: '', 
    coin_cost: 0, 
    is_limited: false, 
    quantity_available: null 
  });
  const [editingPrize, setEditingPrize] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [activeTab, setActiveTab] = useState('admins');
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    fetchAdmins();
    fetchAgents();
    fetchAllUsers();
    fetchPrizes();
    fetchCoinRequests();
  }, []);

  const fetchAdmins = async () => {
    try {
      const response = await axios.get(`${API}/super-admin/users/admins`);
      setAdmins(response.data);
    } catch (error) {
      console.error('Error fetching admins:', error);
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/super-admin/users/agents`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const response = await axios.get(`${API}/super-admin/all-users`);
      setAllUsers(response.data);
    } catch (error) {
      console.error('Error fetching all users:', error);
    }
  };

  const fetchPrizes = async () => {
    try {
      const response = await axios.get(`${API}/super-admin/prizes`);
      setPrizes(response.data);
    } catch (error) {
      console.error('Error fetching prizes:', error);
    }
  };

  const fetchCoinRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/coin-requests`);
      setCoinRequests(response.data);
    } catch (error) {
      console.error('Error fetching coin requests:', error);
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
      setShowCreateAdminForm(false);
      fetchAdmins();
      fetchAllUsers();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating admin');
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/super-admin/agents`, {
        ...newAgent,
        role: 'agent'
      });
      setNewAgent({ username: '', password: '', name: '' });
      setShowCreateAgentForm(false);
      fetchAgents();
      fetchAllUsers();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating agent');
    } finally {
      setLoading(false);
    }
  };

  const createPrize = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/super-admin/prizes`, newPrize);
      setNewPrize({ 
        name: '', 
        description: '', 
        coin_cost: 0, 
        is_limited: false, 
        quantity_available: null 
      });
      setShowCreatePrizeForm(false);
      fetchPrizes();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating prize');
    } finally {
      setLoading(false);
    }
  };

  const updatePrize = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/super-admin/prizes/${editingPrize.id}`, editingPrize);
      setEditingPrize(null);
      setShowEditPrizeForm(false);
      fetchPrizes();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error updating prize');
    } finally {
      setLoading(false);
    }
  };

  const updateUserCredentials = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/super-admin/users/${editingUser.id}/credentials`, {
        username: editingUser.username,
        password: editingUser.password,
        name: editingUser.name
      });
      setEditingUser(null);
      setShowEditUserForm(false);
      fetchAdmins();
      fetchAgents();
      fetchAllUsers();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error updating user credentials');
    } finally {
      setLoading(false);
    }
  };

  const deletePrize = async (prizeId) => {
    if (window.confirm('Are you sure you want to delete this prize?')) {
      try {
        await axios.delete(`${API}/super-admin/prizes/${prizeId}`);
        fetchPrizes();
      } catch (error) {
        alert(error.response?.data?.detail || 'Error deleting prize');
      }
    }
  };

  const deleteAdmin = async (adminId) => {
    if (window.confirm('Are you sure you want to delete this admin?')) {
      try {
        await axios.delete(`${API}/super-admin/admins/${adminId}`);
        fetchAdmins();
        fetchAllUsers();
      } catch (error) {
        alert(error.response?.data?.detail || 'Error deleting admin');
      }
    }
  };

  const approveCoinRequest = async (requestId) => {
    try {
      await axios.put(`${API}/admin/coin-requests/${requestId}/approve`);
      fetchCoinRequests();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error approving coin request');
    }
  };

  const openEditPrizeForm = (prize) => {
    setEditingPrize({ ...prize });
    setShowEditPrizeForm(true);
  };

  const openEditUserForm = (user) => {
    setEditingUser({ 
      ...user, 
      password: '' // Clear password field for security
    });
    setShowEditUserForm(true);
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
          {/* Tab Navigation */}
          <div className="mb-6">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('admins')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'admins'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Admin Management ({admins.length})
              </button>
              <button
                onClick={() => setActiveTab('agents')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'agents'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Agent Management ({agents.length})
              </button>
              <button
                onClick={() => setActiveTab('credentials')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'credentials'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                All User Credentials ({allUsers.length})
              </button>
              <button
                onClick={() => setActiveTab('shop')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'shop'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Shop Management ({prizes.length})
              </button>
              <button
                onClick={() => setActiveTab('coin-requests')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'coin-requests'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Coin Requests ({coinRequests.length})
              </button>
            </nav>
          </div>

          {/* Admin Management Tab */}
          {activeTab === 'admins' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Admin Management</h2>
                  <button
                    onClick={() => setShowCreateAdminForm(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    Create Admin
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
                            onClick={() => openEditUserForm(admin)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Edit
                          </button>
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
          )}

          {/* Agent Management Tab */}
          {activeTab === 'agents' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Agent Management</h2>
                  <button
                    onClick={() => setShowCreateAgentForm(true)}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    Create Agent
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
                          <p className="text-sm text-gray-500">Created: {new Date(agent.created_at).toLocaleDateString()}</p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openEditUserForm(agent)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* All User Credentials Tab */}
          {activeTab === 'credentials' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">All User Credentials</h2>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Admins Section */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Admins ({admins.length})</h3>
                    {admins.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No admins</p>
                    ) : (
                      <div className="space-y-3">
                        {admins.map((admin) => (
                          <div key={admin.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-medium text-gray-900">{admin.name || admin.username}</h4>
                                <p className="text-sm text-gray-600">Username: {admin.username}</p>
                                <p className="text-sm text-gray-600">Role: Admin</p>
                              </div>
                              <button
                                onClick={() => openEditUserForm(admin)}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
                              >
                                Edit
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Agents Section */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Agents ({agents.length})</h3>
                    {agents.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No agents</p>
                    ) : (
                      <div className="space-y-3">
                        {agents.map((agent) => (
                          <div key={agent.id} className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-medium text-gray-900">{agent.name || agent.username}</h4>
                                <p className="text-sm text-gray-600">Username: {agent.username}</p>
                                <p className="text-sm text-gray-600">Role: Agent</p>
                                <p className="text-sm text-gray-600">Coins: {agent.coins || 0} | Deposits: {agent.deposits || 0}</p>
                              </div>
                              <button
                                onClick={() => openEditUserForm(agent)}
                                className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                              >
                                Edit
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
          )}

          {/* Shop Management Tab */}
          {activeTab === 'shop' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">Shop Management</h2>
                  <button
                    onClick={() => setShowCreatePrizeForm(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  >
                    Create Prize
                  </button>
                </div>
              </div>

              <div className="p-6">
                {prizes.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No prizes created yet</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {prizes.map((prize) => (
                      <div key={prize.id} className="border border-gray-200 rounded-lg p-4">
                        <h3 className="font-medium text-gray-900">{prize.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{prize.description}</p>
                        <div className="mt-3 space-y-1">
                          <div className="text-lg font-bold text-purple-600">{prize.coin_cost} coins</div>
                          <div className="text-sm text-gray-500">
                            {prize.is_limited ? `Limited: ${prize.quantity_available} left` : 'Unlimited'}
                          </div>
                          <div className="text-sm text-gray-500">
                            Status: {prize.is_active ? 'Active' : 'Inactive'}
                          </div>
                        </div>
                        <div className="mt-3 flex space-x-2">
                          <button
                            onClick={() => openEditPrizeForm(prize)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => deletePrize(prize.id)}
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
          )}

          {/* Coin Requests Tab */}
          {activeTab === 'coin-requests' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Pending Coin Requests</h2>
              </div>

              <div className="p-6">
                {coinRequests.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No pending coin requests</p>
                ) : (
                  <div className="space-y-4">
                    {coinRequests.map((request) => (
                      <div key={request.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">Sale Amount: ${request.sale_amount}</h3>
                          <p className="text-sm text-gray-500">
                            Agent: {request.agent_name || request.agent_username || request.agent_id}
                          </p>
                          <p className="text-sm text-gray-500">Coins: {request.coins_requested} | Deposits: {request.deposits_requested}</p>
                          <p className="text-sm text-gray-500">Requested: {new Date(request.created_at).toLocaleString()}</p>
                        </div>
                        <button
                          onClick={() => approveCoinRequest(request.id)}
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

      {/* Create Admin Modal */}
      {showCreateAdminForm && (
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
                  onClick={() => setShowCreateAdminForm(false)}
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

      {/* Create Agent Modal */}
      {showCreateAgentForm && (
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
                  onClick={() => setShowCreateAgentForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Prize Modal */}
      {showCreatePrizeForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Prize</h3>
            <form onSubmit={createPrize} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prize Name</label>
                <input
                  type="text"
                  value={newPrize.name}
                  onChange={(e) => setNewPrize({...newPrize, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newPrize.description}
                  onChange={(e) => setNewPrize({...newPrize, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Coin Cost</label>
                <input
                  type="number"
                  step="0.1"
                  value={newPrize.coin_cost}
                  onChange={(e) => setNewPrize({...newPrize, coin_cost: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newPrize.is_limited}
                  onChange={(e) => setNewPrize({...newPrize, is_limited: e.target.checked})}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">Limited Quantity</label>
              </div>
              {newPrize.is_limited && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Available Quantity</label>
                  <input
                    type="number"
                    value={newPrize.quantity_available || ''}
                    onChange={(e) => setNewPrize({...newPrize, quantity_available: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              )}
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreatePrizeForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Prize'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Prize Modal */}
      {showEditPrizeForm && editingPrize && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Prize</h3>
            <form onSubmit={updatePrize} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prize Name</label>
                <input
                  type="text"
                  value={editingPrize.name}
                  onChange={(e) => setEditingPrize({...editingPrize, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editingPrize.description}
                  onChange={(e) => setEditingPrize({...editingPrize, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Coin Cost</label>
                <input
                  type="number"
                  step="0.1"
                  value={editingPrize.coin_cost}
                  onChange={(e) => setEditingPrize({...editingPrize, coin_cost: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={editingPrize.is_limited}
                  onChange={(e) => setEditingPrize({...editingPrize, is_limited: e.target.checked})}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">Limited Quantity</label>
              </div>
              {editingPrize.is_limited && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Available Quantity</label>
                  <input
                    type="number"
                    value={editingPrize.quantity_available || ''}
                    onChange={(e) => setEditingPrize({...editingPrize, quantity_available: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              )}
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowEditPrizeForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Prize'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUserForm && editingUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Edit User Credentials</h3>
            <form onSubmit={updateUserCredentials} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={editingUser.username}
                  onChange={(e) => setEditingUser({...editingUser, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password (leave empty to keep current)</label>
                <input
                  type="password"
                  value={editingUser.password}
                  onChange={(e) => setEditingUser({...editingUser, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter new password or leave empty"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editingUser.name || ''}
                  onChange={(e) => setEditingUser({...editingUser, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowEditUserForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update User'}
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
  const [rewardRequests, setRewardRequests] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTargetForm, setShowTargetForm] = useState(false);
  const [newAgent, setNewAgent] = useState({ username: '', password: '', name: '' });
  const [targetAgent, setTargetAgent] = useState({ id: '', target_monthly: 0 });
  const [activeTab, setActiveTab] = useState('agents');
  const [loading, setLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    fetchAgents();
    fetchSaleRequests();
    fetchRewardRequests();
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

  const fetchRewardRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/reward-requests`);
      setRewardRequests(response.data);
    } catch (error) {
      console.error('Error fetching reward requests:', error);
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

  const updateAgentTarget = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`${API}/admin/agents/${targetAgent.id}/target`, {
        target_monthly: targetAgent.target_monthly
      });
      setTargetAgent({ id: '', target_monthly: 0 });
      setShowTargetForm(false);
      fetchAgents();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error updating target');
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

  const approveRewardRequest = async (rewardId) => {
    try {
      await axios.put(`${API}/admin/reward-requests/${rewardId}/approve`);
      fetchRewardRequests();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error approving reward request');
    }
  };

  const openTargetForm = (agent) => {
    setTargetAgent({ id: agent.id, target_monthly: agent.target_monthly || 0 });
    setShowTargetForm(true);
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
              <button
                onClick={() => setActiveTab('rewards')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'rewards'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Reward Requests ({rewardRequests.length})
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
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{agent.name || agent.username}</h3>
                          <p className="text-sm text-gray-500">Username: {agent.username}</p>
                          <div className="text-sm text-gray-500">
                            <span>Coins: {agent.coins || 0} | </span>
                            <span>Deposits: {agent.deposits || 0} | </span>
                            <span>Target: {agent.target_monthly || 0}</span>
                          </div>
                          {agent.target_monthly > 0 && (
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{
                                  width: `${Math.min((agent.deposits || 0) / agent.target_monthly * 100, 100)}%`
                                }}
                              ></div>
                            </div>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openTargetForm(agent)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Set Target
                          </button>
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
                          <p className="text-sm text-gray-500">
                            Agent: {request.agent_name || request.agent_username || request.agent_id}
                          </p>
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

          {/* Reward Requests Tab */}
          {activeTab === 'rewards' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Pending Reward Use Requests</h2>
              </div>

              <div className="p-6">
                {rewardRequests.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No pending reward requests</p>
                ) : (
                  <div className="space-y-4">
                    {rewardRequests.map((reward) => (
                      <div key={reward.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">Prize: {reward.prize_name}</h3>
                          <p className="text-sm text-gray-500">Agent: {reward.agent_name}</p>
                          <p className="text-sm text-gray-500">Redeemed: {new Date(reward.redeemed_at).toLocaleString()}</p>
                        </div>
                        <button
                          onClick={() => approveRewardRequest(reward.id)}
                          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                        >
                          Approve Use
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

      {/* Set Target Modal */}
      {showTargetForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Set Monthly Target</h3>
            <form onSubmit={updateAgentTarget} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Target (Deposits)</label>
                <input
                  type="number"
                  step="0.1"
                  value={targetAgent.target_monthly}
                  onChange={(e) => setTargetAgent({...targetAgent, target_monthly: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowTargetForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Target'}
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
  const [leaderboard, setLeaderboard] = useState([]);
  const [prizes, setPrizes] = useState([]);
  const [rewardBag, setRewardBag] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSale, setSelectedSale] = useState('');
  const [loading, setLoading] = useState(false);
  const { logout, user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
    fetchLeaderboard();
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

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/agent/leaderboard`);
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
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

  const requestUseReward = async (rewardId) => {
    try {
      await axios.post(`${API}/agent/reward-bag/${rewardId}/request-use`);
      fetchRewardBag();
      alert('Use request submitted for admin approval!');
    } catch (error) {
      alert(error.response?.data?.detail || 'Error requesting reward use');
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
                onClick={() => setActiveTab('leaderboard')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'leaderboard'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Leaderboard
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

              {/* Target Progress */}
              {dashboardData.agent_info.target_monthly > 0 && (
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Target Progress</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Target: {dashboardData.agent_info.target_monthly} deposits</span>
                      <span>Current: {dashboardData.agent_info.deposits} deposits</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full ${
                          dashboardData.agent_info.achievement_percentage >= 100 
                            ? 'bg-green-500' 
                            : dashboardData.agent_info.achievement_percentage >= 75 
                              ? 'bg-yellow-500' 
                              : 'bg-blue-500'
                        }`}
                        style={{
                          width: `${Math.min(dashboardData.agent_info.achievement_percentage, 100)}%`
                        }}
                      ></div>
                    </div>
                    <div className="text-center text-lg font-bold text-gray-900">
                      {dashboardData.agent_info.achievement_percentage}% Complete
                    </div>
                  </div>
                </div>
              )}

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

          {/* Leaderboard Tab */}
          {activeTab === 'leaderboard' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Agent Leaderboard</h2>
              </div>
              <div className="p-6">
                {leaderboard.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No leaderboard data available</p>
                ) : (
                  <div className="space-y-4">
                    {leaderboard.map((agent) => (
                      <div 
                        key={agent.name} 
                        className={`flex items-center justify-between p-4 border rounded-lg ${
                          agent.is_current_user ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <div className="flex items-center space-x-4">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                            agent.rank === 1 ? 'bg-yellow-500' :
                            agent.rank === 2 ? 'bg-gray-400' :
                            agent.rank === 3 ? 'bg-orange-500' :
                            'bg-gray-300'
                          }`}>
                            {agent.rank}
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {agent.name} {agent.is_current_user && '(You)'}
                            </h3>
                            <p className="text-sm text-gray-500">
                              Deposits: {agent.deposits} | Coins Redeemed: {agent.coins_redeemed} | Sales: ${agent.total_sales}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
                        <div className="mt-3 space-y-1">
                          <div className="text-lg font-bold text-blue-600">{prize.coin_cost} coins</div>
                          {prize.is_limited && (
                            <div className="text-sm text-gray-500">
                              Limited: {prize.quantity_available} left
                            </div>
                          )}
                        </div>
                        <div className="mt-3">
                          <button
                            onClick={() => redeemPrize(prize.id)}
                            disabled={
                              dashboardData.agent_info.coins < prize.coin_cost ||
                              (prize.is_limited && prize.quantity_available <= 0)
                            }
                            className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 py-2 rounded text-sm font-medium"
                          >
                            {dashboardData.agent_info.coins < prize.coin_cost 
                              ? 'Insufficient Coins' 
                              : (prize.is_limited && prize.quantity_available <= 0)
                                ? 'Out of Stock'
                                : 'Redeem'
                            }
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
                          <p className="text-sm text-gray-500">
                            Status: <span className={`font-medium ${
                              reward.status === 'unused' ? 'text-green-600' :
                              reward.status === 'pending_use' ? 'text-yellow-600' :
                              'text-gray-600'
                            }`}>
                              {reward.status === 'unused' ? 'Ready to Use' :
                               reward.status === 'pending_use' ? 'Pending Admin Approval' :
                               'Used'}
                            </span>
                          </p>
                          <p className="text-sm text-gray-500">Redeemed: {new Date(reward.redeemed_at).toLocaleDateString()}</p>
                          {reward.used_at && (
                            <p className="text-sm text-gray-500">Used: {new Date(reward.used_at).toLocaleDateString()}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          {reward.status === 'unused' && (
                            <button
                              onClick={() => requestUseReward(reward.id)}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                            >
                              Request to Use
                            </button>
                          )}
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
