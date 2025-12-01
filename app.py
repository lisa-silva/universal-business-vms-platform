import React, { useState, useEffect, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged, signOut } from 'firebase/auth';
import { 
  getFirestore, collection, onSnapshot, query, addDoc, serverTimestamp, 
  where, getDocs 
} from 'firebase/firestore';
import { Home, ClipboardList, Settings, Loader2, User, CheckCircle, PlusCircle, Wrench, Package, Mail, XCircle } from 'lucide-react';

// --- Global Constants and Firebase Setup ---

// Mandatory variables provided by the Canvas environment
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : {};
const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;

# The central data path for this application's public data (Generalized)
const VMS_COLLECTION_PATH = `/artifacts/${appId}/public/data/universal_vms`;

// Initialize Firebase App and Services
let app, db, auth;
if (Object.keys(firebaseConfig).length > 0) {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  auth = getAuth(app);
}

// --- Component: Custom Modal Message ---
const MessageModal = ({ message, type, onClose }) => (
  <div className="fixed inset-0 bg-gray-900 bg-opacity-75 z-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-xl shadow-2xl p-6 max-w-sm w-full transform transition-all duration-300 scale-100">
      <div className="flex items-center space-x-3">
        {type === 'success' && <CheckCircle className="w-6 h-6 text-green-600" />}
        {type === 'error' && <XCircle className="w-6 h-6 text-red-600" />}
        <h3 className="text-lg font-semibold text-gray-900">
          {type === 'success' ? 'Success!' : 'Error'}
        </h3>
      </div>
      <p className="mt-2 text-sm text-gray-600">{message}</p>
      <div className="mt-4 flex justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Close
        </button>
      </div>
    </div>
  </div>
);

// --- Main Application Component ---
const App = () => {
  // State for Auth and User
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [userId, setUserId] = useState(null);

  // State for Navigation and Data
  const [currentView, setCurrentView] = useState('QuoteBuilder');
  const [quotes, setQuotes] = useState([]);
  const [maintenanceRecords, setMaintenanceRecords] = useState([]);
  const [isLoadingData, setIsLoadingData] = useState(false);

  // State for Notifications
  const [modalMessage, setModalMessage] = useState(null);
  const [modalType, setModalType] = useState('success');

  const showMessage = (message, type = 'success') => {
    setModalMessage(message);
    setModalType(type);
  };

  const closeModal = () => {
    setModalMessage(null);
  };

  // 1. Firebase Authentication Effect
  useEffect(() => {
    if (!auth) {
      console.error("Firebase Auth not initialized.");
      // Set AuthReady true but userId null if Firebase is not configured
      setIsAuthReady(true); 
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        setUserId(user.uid);
      } else {
        // Sign in if no user is authenticated
        try {
          if (initialAuthToken) {
            await signInWithCustomToken(auth, initialAuthToken);
          } else {
            await signInAnonymously(auth);
          }
        } catch (error) {
          console.error("Authentication failed:", error);
          showMessage("Failed to connect to the demo service.", 'error');
        }
      }
      setIsAuthReady(true);
    });

    return () => unsubscribe();
  }, []);

  // 2. Data Listener Effect (Runs only when Auth is ready)
  useEffect(() => {
    if (!isAuthReady || !db || !userId) return; // Wait for both Auth readiness AND a valid userId

    setIsLoadingData(true);

    const q = query(collection(db, VMS_COLLECTION_PATH));

    // onSnapshot listener for real-time updates
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const allDocs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      
      const newQuotes = allDocs
        .filter(doc => doc.type === 'quote')
        .sort((a, b) => (b.timestamp?.toMillis() || 0) - (a.timestamp?.toMillis() || 0));

      const newMaintenanceRecords = allDocs
        .filter(doc => doc.type === 'maintenanceRecord')
        .sort((a, b) => (b.timestamp?.toMillis() || 0) - (a.timestamp?.toMillis() || 0));
        
      setQuotes(newQuotes);
      setMaintenanceRecords(newMaintenanceRecords);
      setIsLoadingData(false);
    }, (error) => {
      console.error("Error fetching data:", error);
      showMessage("Error loading VMS data.", 'error');
      setIsLoadingData(false);
    });

    return () => unsubscribe();
  }, [isAuthReady, db, userId]); // Added userId as dependency for better control


  // --- Data Submission Functions ---
  const submitQuote = async (data) => {
    if (!db || !userId) {
      showMessage("System not ready. Please wait for authentication.", 'error');
      return;
    }
    
    try {
      await addDoc(collection(db, VMS_COLLECTION_PATH), {
        ...data,
        type: 'quote',
        timestamp: serverTimestamp(),
        submitterId: userId,
        status: 'New'
      });
      showMessage("Your service request has been submitted successfully!");
    } catch (e) {
      console.error("Error adding quote document: ", e);
      showMessage("Failed to submit service request. Please try again.", 'error');
    }
  };

  const submitMaintenanceRecord = async (data) => {
    if (!db || !userId) {
      showMessage("System not ready. Please wait for authentication.", 'error');
      return;
    }
    
    try {
      await addDoc(collection(db, VMS_COLLECTION_PATH), {
        ...data,
        type: 'maintenanceRecord',
        timestamp: serverTimestamp(),
        submitterId: userId,
      });
      showMessage("Asset registered successfully!");
    } catch (e) {
      console.error("Error adding maintenance record: ", e);
      showMessage("Failed to register asset. Please try again.", 'error');
    }
  };

  // --- View Components ---

  const NavItem = ({ viewName, icon: Icon, label }) => (
    <button
      onClick={() => setCurrentView(viewName)}
      className={`flex flex-col items-center justify-center p-3 sm:p-4 text-xs sm:text-sm font-medium transition duration-200 rounded-lg hover:bg-blue-100 ${
        currentView === viewName ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-blue-600'
      }`}
    >
      <Icon className="w-5 h-5 sm:w-6 sm:h-6 mb-1" />
      <span className="hidden sm:block">{label}</span>
    </button>
  );

  const QuoteBuilder = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [serviceType, setServiceType] = useState('Service A');
    const [description, setDescription] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setIsSubmitting(true);
      await submitQuote({ name, email, serviceType, description });
      // Reset form on success
      setName('');
      setEmail('');
      setServiceType('Service A');
      setDescription('');
      setIsSubmitting(false);
    };

    return (
      <div className="p-6 bg-white shadow-lg rounded-xl">
        <h2 className="text-3xl font-bold text-gray-800 mb-6 border-b pb-2">Submit Service Request</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="clientName" className="block text-sm font-medium text-gray-700">Client Name</label>
            <input
              type="text"
              id="clientName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3"
              placeholder="John Smith"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3"
              placeholder="john@example.com"
            />
          </div>
          <div>
            <label htmlFor="serviceType" className="block text-sm font-medium text-gray-700">Service Type</label>
            <select
              id="serviceType"
              value={serviceType}
              onChange={(e) => setServiceType(e.target.value)}
              required
              className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3 bg-white"
            >
              <option>Service A (Initial Consultation)</option>
              <option>Service B (Routine Maintenance)</option>
              <option>Service C (Component Replacement)</option>
              <option>Emergency Support</option>
            </select>
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Problem / Request Description</label>
            <textarea
              id="description"
              rows="4"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3"
              placeholder="Describe the issue or service needed in detail..."
            ></textarea>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || !isAuthReady}
            className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-base font-medium text-white transition duration-150 ${
              isSubmitting || !isAuthReady ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
            }`}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Submitting...
              </>
            ) : (
              <>
                <ClipboardList className="w-5 h-5 mr-2" /> Submit Request
              </>
            )}
          </button>
          {!isAuthReady && <p className="text-center text-sm text-red-500 mt-2">Connecting to service...</p>}
        </form>
      </div>
    );
  };

  const CustomerPortal = () => {
    const [applianceType, setApplianceType] = useState('Asset Type A');
    const [modelNumber, setModelNumber] = useState('');
    const [installDate, setInstallDate] = useState(new Date().toISOString().substring(0, 10));
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Filter records specific to the current authenticated user for a realistic portal view
    const userMaintenanceRecords = maintenanceRecords.filter(r => r.submitterId === userId);
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      setIsSubmitting(true);
      await submitMaintenanceRecord({ applianceType, modelNumber, installDate });
      // Reset form on success
      setApplianceType('Asset Type A');
      setModelNumber('');
      setInstallDate(new Date().toISOString().substring(0, 10));
      setIsSubmitting(false);
    };

    return (
      <div className="p-6 bg-white shadow-lg rounded-xl space-y-8">
        <h2 className="text-3xl font-bold text-gray-800 border-b pb-2">Your Customer Asset Portal</h2>
        <div className="bg-gray-50 p-4 rounded-lg shadow-inner">
            <p className="flex items-center text-sm font-medium text-gray-700">
                <User className="w-4 h-4 mr-2 text-blue-500"/>
                Your Demo ID: <code className="ml-2 font-mono text-xs p-1 bg-white rounded">{userId || 'Loading...'}</code>
            </p>
        </div>
        
        {/* Register New Asset */}
        <div className="border border-green-200 bg-green-50 p-6 rounded-xl">
            <h3 className="text-xl font-semibold text-green-700 flex items-center mb-4"><PlusCircle className="w-5 h-5 mr-2"/> Register New Asset/Equipment</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="applianceType" className="block text-sm font-medium text-gray-700">Asset Type</label>
                    <select
                        id="applianceType"
                        value={applianceType}
                        onChange={(e) => setApplianceType(e.target.value)}
                        required
                        className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 p-3 bg-white"
                    >
                        <option>Asset Type A (Large System)</option>
                        <option>Asset Type B (Small Component)</option>
                        <option>Asset Type C (Software License)</option>
                        <option>Specialized Unit</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="modelNumber" className="block text-sm font-medium text-gray-700">Model / Serial Number</label>
                    <input
                        type="text"
                        id="modelNumber"
                        value={modelNumber}
                        onChange={(e) => setModelNumber(e.target.value)}
                        required
                        className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 p-3"
                        placeholder="SERIAL-XYZ-12345"
                    />
                </div>
                <div>
                    <label htmlFor="installDate" className="block text-sm font-medium text-gray-700">Setup / Purchase Date</label>
                    <input
                        type="date"
                        id="installDate"
                        value={installDate}
                        onChange={(e) => setInstallDate(e.target.value)}
                        required
                        className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 p-3"
                    />
                </div>
                <button
                    type="submit"
                    disabled={isSubmitting || !isAuthReady}
                    className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-base font-medium text-white transition duration-150 ${
                        isSubmitting || !isAuthReady ? 'bg-green-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
                    }`}
                >
                    {isSubmitting ? (
                        <>
                            <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Registering...
                        </>
                    ) : (
                        <>
                            <Wrench className="w-5 h-5 mr-2" /> Register Asset
                        </>
                    )}
                </button>
                {!isAuthReady && <p className="text-center text-sm text-red-500 mt-2">Connecting to service...</p>}
            </form>
        </div>

        {/* Display Registered Assets */}
        <div className="pt-4">
            <h3 className="text-xl font-semibold text-gray-800 mb-4 border-b pb-2 flex items-center"><Package className="w-5 h-5 mr-2"/> Your Registered Assets ({userMaintenanceRecords.length})</h3>
            {userMaintenanceRecords.length === 0 ? (
                <p className="text-gray-500 italic">No assets registered yet. Use the form above!</p>
            ) : (
                <div className="space-y-3">
                    {userMaintenanceRecords.map((record) => (
                        <div key={record.id} className="bg-gray-100 p-4 rounded-lg shadow-sm border border-gray-200">
                            <p className="font-semibold text-gray-800">{record.applianceType}</p>
                            <p className="text-sm text-gray-600">Model/Serial: {record.modelNumber}</p>
                            <p className="text-xs text-gray-500">Setup Date: {record.installDate}</p>
                            <p className="text-xs text-gray-500">Recorded By ID: <code className="font-mono">{record.submitterId.substring(0, 8)}...</code></p>
                        </div>
                    ))}
                </div>
            )}
        </div>
      </div>
    );
  };

  const AdminDashboard = () => {
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      // Convert Firebase Timestamp object to Date and format
      const date = timestamp.toDate();
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    };

    const StatusBadge = ({ status }) => {
        let color = 'bg-gray-200 text-gray-800';
        if (status === 'New') color = 'bg-red-100 text-red-700';
        if (status === 'Quoted') color = 'bg-yellow-100 text-yellow-700';
        if (status === 'Completed') color = 'bg-green-100 text-green-700';
        return <span className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full ${color}`}>{status}</span>;
    };


    return (
      <div className="p-6 bg-white shadow-lg rounded-xl space-y-10">
        <h2 className="text-3xl font-bold text-gray-800 border-b pb-2 flex items-center">
            <Settings className="w-7 h-7 mr-2 text-blue-600"/> Administration Panel
        </h2>
        <div className="bg-gray-50 p-4 rounded-lg shadow-inner">
            <p className="flex items-center text-sm font-medium text-gray-700">
                <User className="w-4 h-4 mr-2 text-blue-500"/>
                Your Demo ID: <code className="ml-2 font-mono text-xs p-1 bg-white rounded">{userId || 'Loading...'}</code>
            </p>
            <p className="text-xs text-gray-500 mt-1">This ID is visible because the demo data is public.</p>
        </div>

        {/* Quote/Service Requests */}
        <div>
          <h3 className="text-2xl font-semibold text-red-700 mb-4 flex items-center"><Mail className="w-5 h-5 mr-2"/> Service Requests ({quotes.length})</h3>
          {isLoadingData ? (
            <div className="flex justify-center items-center p-8 text-gray-500">
              <Loader2 className="w-6 h-6 mr-2 animate-spin" /> Loading Requests...
            </div>
          ) : quotes.length === 0 ? (
            <p className="text-gray-500 italic">No new service requests submitted yet.</p>
          ) : (
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client / Email</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Service Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">Description</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">Submitted</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {quotes.map((quote) => (
                    <tr key={quote.id}>
                        <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{quote.name}</div>
                            <div className="text-xs text-gray-500">{quote.email}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{quote.serviceType}</td>
                        <td className="px-4 py-4 text-sm text-gray-500 max-w-xs truncate hidden sm:table-cell">{quote.description}</td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 hidden sm:table-cell">{formatTimestamp(quote.timestamp)}</td>
                        <td className="px-4 py-4 whitespace-nowrap">
                            <StatusBadge status={quote.status} />
                        </td>
                    </tr>
                    ))}
                </tbody>
                </table>
            </div>
          )}
        </div>

        {/* Maintenance Records */}
        <div>
          <h3 className="text-2xl font-semibold text-green-700 mb-4 flex items-center"><Package className="w-5 h-5 mr-2"/> All Registered Assets ({maintenanceRecords.length})</h3>
          {isLoadingData ? (
            <div className="flex justify-center items-center p-8 text-gray-500">
              <Loader2 className="w-6 h-6 mr-2 animate-spin" /> Loading Records...
            </div>
          ) : maintenanceRecords.length === 0 ? (
            <p className="text-gray-500 italic">No assets have been registered yet.</p>
          ) : (
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asset Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model / Serial No.</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">Setup Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">Customer ID</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {maintenanceRecords.map((record) => (
                    <tr key={record.id}>
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{record.applianceType}</td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{record.modelNumber}</td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 hidden sm:table-cell">{record.installDate}</td>
                        <td className="px-4 py-4 whitespace-nowrap text-xs text-gray-500 hidden sm:table-cell">
                           <code className="font-mono p-1 bg-gray-100 rounded">{record.submitterId.substring(0, 8)}...</code>
                        </td>
                    </tr>
                    ))}
                </tbody>
                </table>
            </div>
          )}
        </div>
      </div>
    );
  };


  // --- Render Logic ---
  const renderView = () => {
    if (!isAuthReady) {
      return (
        <div className="flex flex-col items-center justify-center h-64">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
          <p className="mt-4 text-lg text-gray-600">Connecting to VMS Backend...</p>
        </div>
      );
    }
    
    switch (currentView) {
      case 'QuoteBuilder':
        return <QuoteBuilder />;
      case 'CustomerPortal':
        return <CustomerPortal />;
      case 'AdminDashboard':
        return <AdminDashboard />;
      default:
        return <QuoteBuilder />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 font-sans antialiased flex flex-col items-center p-4 sm:p-8">
      {modalMessage && <MessageModal message={modalMessage} type={modalType} onClose={closeModal} />}

      <header className="w-full max-w-5xl bg-white shadow-xl rounded-xl p-4 mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-4 text-center">Universal Service Management (VMS) Demo</h1>
        <nav className="flex justify-around border-t border-b py-2">
          <NavItem viewName="QuoteBuilder" icon={ClipboardList} label="Service Request (Public)" />
          <NavItem viewName="CustomerPortal" icon={Home} label="Customer Asset Portal" />
          <NavItem viewName="AdminDashboard" icon={Settings} label="Admin Panel" />
        </nav>
      </header>

      <main className="w-full max-w-5xl">
        {renderView()}
      </main>
    </div>
  );
};

export default App;
