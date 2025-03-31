import streamlit as st
import spacy
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Must be the first Streamlit command
st.set_page_config(
    page_title="NewsNex - From News to Next Opportunities",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS and JavaScript for styling and 3D globe
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0;
    }
    .tagline {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .sub-tagline {
        font-size: 1.1rem;
        color: #6B7280;
        font-style: italic;
    }
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #1E40AF;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    .metric-title {
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        color: rgba(255, 255, 255, 0.9);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }
    .metric-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    #globe-container {
        width: 100%;
        height: 300px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
        border-radius: 10px;
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 100rem;
    }
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        }
        .metric-title {
            color: rgba(255, 255, 255, 0.95);
        }
    }
</style>

<!-- Add Three.js library -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
    // Globe visualization
    function createGlobe() {
        const container = document.getElementById('globe-container');
        if (!container) return;  // Exit if container not found

        const width = container.offsetWidth;
        const height = container.offsetHeight;

        // Setup scene
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        
        renderer.setSize(width, height);
        container.appendChild(renderer.domElement);

        // Create globe with particles
        const geometry = new THREE.SphereGeometry(5, 64, 64);
        const vertices = [];
        const positions = geometry.attributes.position.array;

        for (let i = 0; i < positions.length; i += 3) {
            vertices.push(
                positions[i],
                positions[i + 1],
                positions[i + 2]
            );
        }

        const particleGeometry = new THREE.BufferGeometry();
        particleGeometry.setAttribute(
            'position',
            new THREE.Float32BufferAttribute(vertices, 3)
        );

        const material = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.05,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        const globe = new THREE.Points(particleGeometry, material);
        scene.add(globe);

        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        // Add point light
        const pointLight = new THREE.PointLight(0xffffff, 1);
        pointLight.position.set(10, 10, 10);
        scene.add(pointLight);

        camera.position.z = 8;

        // Animation
        function animate() {
            requestAnimationFrame(animate);
            globe.rotation.y += 0.002;
            renderer.render(scene, camera);
        }

        animate();

        // Handle window resize
        window.addEventListener('resize', () => {
            const newWidth = container.offsetWidth;
            const newHeight = container.offsetHeight;
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(newWidth, newHeight);
        });

        // Add interactivity
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };

        container.addEventListener('mousedown', (e) => {
            isDragging = true;
            previousMousePosition = {
                x: e.clientX,
                y: e.clientY
            };
        });

        container.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const deltaMove = {
                x: e.clientX - previousMousePosition.x,
                y: e.clientY - previousMousePosition.y
            };

            globe.rotation.y += deltaMove.x * 0.005;
            globe.rotation.x += deltaMove.y * 0.005;

            previousMousePosition = {
                x: e.clientX,
                y: e.clientY
            };
        });

        container.addEventListener('mouseup', () => {
            isDragging = false;
        });

        container.addEventListener('mouseleave', () => {
            isDragging = false;
        });
    }

    // Initialize globe when document is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createGlobe);
    } else {
        createGlobe();
    }
</script>
""", unsafe_allow_html=True)

# Rest of your Python imports and class definitions remain the same...

def main():
    # Updated header with new branding
    st.markdown('<p class="main-title">🎯 NewsNex</p>', unsafe_allow_html=True)
    st.markdown('<p class="tagline">Where News Sparks the Next Deal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-tagline">🧠 Smarter Prospecting Starts with News</p>', unsafe_allow_html=True)
    
    # Add 3D Globe
    st.markdown('<div id="globe-container"></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Rest of your main() function remains the same...

# Rest of your code remains the same...
