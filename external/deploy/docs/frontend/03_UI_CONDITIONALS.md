# Feature-Based UI Implementation

## 🎯 **Core Pattern**
Show/hide UI sections based on backend features:

```javascript
import { BACKEND_TEMPLATES } from '../config/backend_templates';

const BackendDashboard = ({ backend }) => {
  const features = BACKEND_TEMPLATES[backend.type].features;
  const capabilities = BACKEND_TEMPLATES[backend.type].capabilities;

  return (
    <div className="backend-dashboard">
      {/* Always show basic info */}
      <BackendInfo backend={backend} />
      
      {/* Always show if supported */}
      {features.prompt_management && (
        <PromptEditor backend={backend} />
      )}
      
      {/* AAF-only features */}
      {features.demo_management && (
        <DemoManagement backend={backend} />
      )}
      
      {features.knowledge_base && (
        <KnowledgeBase backend={backend} />
      )}
      
      {features.multi_tools && (
        <ToolsConfiguration backend={backend} />
      )}
      
      {features.config_editor && (
        <ConfigEditor backend={backend} />
      )}
      
      {/* Action buttons based on capabilities */}
      <ActionButtons>
        {capabilities.create && (
          <CreateButton onClick={handleCreate} />
        )}
        {capabilities.delete && (
          <DeleteButton onClick={handleDelete} />
        )}
        {capabilities.remove_from_admin && (
          <RemoveFromAdminButton onClick={handleRemove} />
        )}
      </ActionButtons>
    </div>
  );
};
```

## 🧩 **Component Examples**

### **Conditional Navigation**
```javascript
const Navigation = ({ currentBackendType }) => {
  const features = BACKEND_TEMPLATES[currentBackendType].features;
  
  return (
    <nav>
      <NavItem to="/prompts">Prompts</NavItem>
      {features.demo_management && (
        <NavItem to="/demos">Demos</NavItem>
      )}
      {features.knowledge_base && (
        <NavItem to="/knowledge">Knowledge Base</NavItem>
      )}
      {features.multi_tools && (
        <NavItem to="/tools">Tools</NavItem>
      )}
    </nav>
  );
};
```

### **Feature Cards**
```javascript
const FeatureCards = ({ backendType }) => {
  const features = BACKEND_TEMPLATES[backendType].features;
  
  const availableFeatures = Object.entries(features)
    .filter(([_, enabled]) => enabled)
    .map(([feature, _]) => feature);
    
  return (
    <div className="feature-grid">
      {availableFeatures.map(feature => (
        <FeatureCard key={feature} feature={feature} />
      ))}
    </div>
  );
};
```

## ⚠️ **Important Notes**
- **Always check features** before rendering components
- **Custom backends** only show prompt management
- **AAF backends** show all features
- **Gracefully handle** missing features (don't crash)
