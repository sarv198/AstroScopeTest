import numpy as np

# You can retreive orbital paramters from SBDB API 

def orbital_elements_to_ellipsecurve(a, e, i_deg, RAAN_deg, argp_deg, earth_pos=(0,0)):
    """
    Converts orbital elements into Three.js EllipseCurve parameters.
    
    Returns:
        dict with keys: aX, aY, xRadius, yRadius, aStartAngle, aEndAngle, aRotation
    """
    # Semi-minor axis
    b = a * np.sqrt(1 - e**2)
    
    # Euler angles for rotation from perifocal -> ECI
    i = np.radians(i_deg)
    Ω = np.radians(RAAN_deg)
    ω = np.radians(argp_deg)
    
    # Rotation matrices
    def R3(theta):
        c, s = np.cos(theta), np.sin(theta)
        return np.array([[ c, -s, 0],
                         [ s,  c, 0],
                         [ 0,  0, 1]])
    def R1(theta):
        c, s = np.cos(theta), np.sin(theta)
        return np.array([[1, 0,  0],
                         [0, c, -s],
                         [0, s,  c]])
    
    # Full rotation from perifocal to ECI
    Q = R3(Ω) @ R1(i) @ R3(ω)
    
    # Sample points along ellipse in perifocal plane
    nu = np.linspace(0, 2*np.pi, 200)  # true anomaly
    r = a*(1 - e**2)/(1 + e*np.cos(nu))
    x_pf = r * np.cos(nu)
    y_pf = r * np.sin(nu)
    z_pf = np.zeros_like(nu)
    points_pf = np.vstack((x_pf, y_pf, z_pf))  # shape (3,N)
    
    # Rotate to ECI
    points_eci = Q @ points_pf  # shape (3,N)
    
    # Project onto XY plane for Three.js
    x_proj = points_eci[0,:] - earth_pos[0]
    y_proj = points_eci[1,:] - earth_pos[1]
    
    # Compute ellipse parameters from projected points
    xRadius = (np.max(x_proj) - np.min(x_proj))/2
    yRadius = (np.max(y_proj) - np.min(y_proj))/2
    aX = np.mean(x_proj)
    aY = np.mean(y_proj)
    
    # Rotation: angle of major axis relative to X
    # Use PCA to estimate rotation
    coords = np.vstack((x_proj, y_proj))
    cov = np.cov(coords)
    eigvals, eigvecs = np.linalg.eig(cov)
    major_axis_vec = eigvecs[:, np.argmax(eigvals)]
    aRotation = np.arctan2(major_axis_vec[1], major_axis_vec[0])
    
    return {
        "aX": float(aX),
        "aY": float(aY),
        "xRadius": float(xRadius),
        "yRadius": float(yRadius),
        "aStartAngle": 0,
        "aEndAngle": 2*np.pi,
        "aClockwise": False,
        "aRotation": float(aRotation)
    }





