import React, { useEffect, useState } from 'react';
import Project from '../components/Project';
import Checkout from '../components/Checkout';

const MyUserPortal = () => {
  const [activeProject, setActiveProject] = useState(null);
  const [projects, setProjects] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newProject, setNewProject] = useState({ projectId: '', name: '', description: '' });
  const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

  useEffect(() => {
    if (!currentUser?.userId) return;
    fetch(`http://127.0.0.1:5000/get_user_projects_list/${currentUser.userId}`)
      .then(response => response.json())
      .then(setProjects)
      .catch(() => alert('Could not load your projects.'));
  }, [currentUser?.userId]);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!currentUser?.userId) {
      alert('Please sign in again before creating a project.');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/create_project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newProject, ownerId: currentUser.userId })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not create project');
      setProjects(previous => [...previous, data]);
      setNewProject({ projectId: '', name: '', description: '' });
      setShowCreateForm(false);
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div>
      <div className="portal-header">
        <div>
          <h1 style={{color: 'var(--ut-burnt-orange)'}}>My Workspace</h1>
          <p>Manage your projects and request hardware from the UT Austin Makerspace.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateForm(previous => !previous)}>
          + Create New Project
        </button>
      </div>

      {showCreateForm && (
        <form className="card auth-form" onSubmit={handleCreateProject}>
          <h3>Create Project</h3>
          <div className="form-group">
            <label className="form-label" htmlFor="projectId">Project ID</label>
            <input className="form-control" id="projectId" value={newProject.projectId}
              onChange={(e) => setNewProject({ ...newProject, projectId: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="projectName">Project Name</label>
            <input className="form-control" id="projectName" value={newProject.name}
              onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="projectDescription">Description</label>
            <textarea className="form-control" id="projectDescription" value={newProject.description}
              onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary">Create Project</button>
        </form>
      )}
      
      {activeProject ? (
        <div>
          <button className="btn btn-secondary" style={{marginBottom: '1rem'}} onClick={() => setActiveProject(null)}>
            &larr; Back to Projects
          </button>
          <Checkout project={activeProject} />
        </div>
      ) : (
        <div className="dashboard-grid">
          {projects.map(proj => (
            <div key={proj.projectId} onClick={() => setActiveProject(proj)} style={{cursor: 'pointer'}}>
              <Project project={proj} />
            </div>
          ))}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', borderStyle: 'dashed', borderWidth: '2px', borderColor: 'var(--ut-dark-gray)', cursor: 'pointer', background: 'transparent', boxShadow: 'none' }}>
            <h3 style={{ color: 'var(--ut-charcoal)', opacity: 0.7 }}>Join Existing Project</h3>
            <p style={{ opacity: 0.6 }}>Enter a project ID to collaborate</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyUserPortal;

