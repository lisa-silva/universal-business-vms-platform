Universal Service Management (VMS) Demo Platform

This is a single-file React application designed as a universal template for any business that needs to manage customer service requests and track associated assets or equipment. It is built to be fully responsive and uses Google's Firestore for real-time data persistence and management.

Core Features

This platform is divided into three main operational views, accessible via the central navigation bar:

1. Service Request (Public)

This view allows customers or internal users to submit detailed requests for service (e.g., initial consultations, routine maintenance, emergency support).

Functionality: Collects client name, email, chosen service type, and a detailed description of the issue or need.

Data Storage: Submits the request as a quote type document to the Firestore database for administrative review.

2. Customer Asset Portal

This view provides customers with a centralized location to register and view their assets/equipment, establishing a service history context.

Functionality: Allows users (identified by their unique, anonymous session ID) to register new assets by specifying the Asset Type, Model/Serial Number, and Setup/Purchase Date.

Asset Tracking: Displays a list of all assets previously registered by the current user's unique ID.

3. Administration Panel

This dashboard provides a complete overview of all system activity, simulating the view an administrator would use.

Service Request Tracking: Displays all incoming service requests in a table format, including client details, service type, and submission time, allowing staff to manage workflow (status is currently static but expandable).

Asset Registry: Displays a comprehensive list of all assets registered across all customer IDs, including model/serial information and setup dates.

Technology Stack

Frontend: React (functional components and hooks)

Styling: Tailwind CSS (utility-first approach)

Database: Google Cloud Firestore (real-time data synchronization)

Authentication: Firebase Auth (handles anonymous or custom token sign-in for demo purposes)

Deployment: Designed to run as a single, self-contained file.

Data Structure

All transactional data (quotes and maintenance records) are stored in a single public Firestore collection to simplify the demo environment, allowing all authenticated users to view the "Admin" panel. Each document contains a type field (quote or maintenanceRecord) for easy filtering.
