import {
    BrowserRouter,
    NavLink,
    Route,
    Routes,
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import JobExplorer from "./pages/JobExplorer";
import JobDetail from "./pages/JobDetail";
import Intelligence from "./pages/Intelligence";


function App() {
    return (
        <BrowserRouter>

            {/* =================================================
                MAIN NAVIGATION
            ================================================= */}

            <nav className="main-nav">

                <div className="nav-brand">
                    AI Job Market Intelligence
                </div>


                <div className="nav-links">

                    {/* Dashboard */}

                    <NavLink
                        to="/"
                        end
                        className={({ isActive }) =>
                            isActive
                                ? "nav-link active"
                                : "nav-link"
                        }
                    >
                        Dashboard
                    </NavLink>


                    {/* Job Explorer */}

                    <NavLink
                        to="/jobs"
                        className={({ isActive }) =>
                            isActive
                                ? "nav-link active"
                                : "nav-link"
                        }
                    >
                        Job Explorer
                    </NavLink>


                    {/* Market Intelligence */}

                    <NavLink
                        to="/intelligence"
                        className={({ isActive }) =>
                            isActive
                                ? "nav-link active"
                                : "nav-link"
                        }
                    >
                        Ask AI
                    </NavLink>

                </div>

            </nav>


            {/* =================================================
                ROUTES
            ================================================= */}

            <Routes>

                {/* Dashboard */}

                <Route
                    path="/"
                    element={<Dashboard />}
                />


                {/* Job Explorer */}

                <Route
                    path="/jobs"
                    element={<JobExplorer />}
                />


                {/* Job Details */}

                <Route
                    path="/jobs/:jobId"
                    element={<JobDetail />}
                />


                {/* AI Market Intelligence */}

                <Route
                    path="/intelligence"
                    element={<Intelligence />}
                />

            </Routes>

        </BrowserRouter>
    );
}


export default App;