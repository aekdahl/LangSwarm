# Prompt Editor Implementation

## 🎯 **Purpose** 
The prompt editor is the **core shared feature** between AAF and custom backends. Every backend type supports prompt management.

## 🧩 **Component Structure**

```javascript
const PromptEditor = ({ backend }) => {
  const [prompts, setPrompts] = useState({});
  const [schema, setSchema] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPromptSchema();
    loadCurrentPrompts();
  }, [backend.id]);

  const loadPromptSchema = async () => {
    // Get what prompts can be edited
    const response = await fetch(`${API.backends}/${backend.id}/prompts/schema`);
    setSchema(await response.json());
  };

  const loadCurrentPrompts = async () => {
    // Get current prompt values
    const response = await fetch(`${API.backends}/${backend.id}/prompts`);
    setPrompts(await response.json());
  };

  const savePrompts = async () => {
    setLoading(true);
    try {
      await fetch(`${API.backends}/${backend.id}/prompts`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prompts)
      });
      showSuccess('Prompts updated successfully');
    } catch (error) {
      showError('Failed to update prompts');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prompt-editor">
      <h3>Prompt Configuration</h3>
      
      {schema.fields?.map(field => (
        <PromptField
          key={field.name}
          field={field}
          value={prompts[field.name] || field.default || ''}
          onChange={(value) => setPrompts(prev => ({
            ...prev,
            [field.name]: value
          }))}
        />
      ))}
      
      <button 
        onClick={savePrompts} 
        disabled={loading}
        className="save-button"
      >
        {loading ? 'Saving...' : 'Save Prompts'}
      </button>
    </div>
  );
};
```

## 🔧 **Field Types**

### **Text Field**
```javascript
const TextField = ({ field, value, onChange }) => (
  <div className="field">
    <label>{field.label}</label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      required={field.required}
    />
    {field.description && (
      <small>{field.description}</small>
    )}
  </div>
);
```

### **Textarea Field**
```javascript
const TextareaField = ({ field, value, onChange }) => (
  <div className="field">
    <label>{field.label}</label>
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      required={field.required}
      rows={field.rows || 4}
    />
    {field.description && (
      <small>{field.description}</small>
    )}
  </div>
);
```

### **Select Field**
```javascript
const SelectField = ({ field, value, onChange }) => (
  <div className="field">
    <label>{field.label}</label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={field.required}
    >
      <option value="">Select...</option>
      {field.options.map(option => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
    {field.description && (
      <small>{field.description}</small>
    )}
  </div>
);
```

## 📋 **Schema Example**

```javascript
// What the backend returns from /api/prompts/schema
{
  "fields": [
    {
      "name": "system_prompt",
      "label": "System Prompt", 
      "type": "textarea",
      "required": true,
      "placeholder": "You are a helpful assistant...",
      "description": "Main AI behavior prompt",
      "rows": 6
    },
    {
      "name": "assistant_name",
      "label": "Assistant Name",
      "type": "text", 
      "default": "AI Assistant",
      "description": "How the AI identifies itself"
    },
    {
      "name": "response_style",
      "label": "Response Style",
      "type": "select",
      "options": ["professional", "casual", "technical"],
      "default": "professional"
    }
  ]
}
```

## ✅ **Best Practices**
- **Always load schema first** to know what fields to show
- **Show field descriptions** to help users understand prompts
- **Validate required fields** before saving
- **Show loading states** during save operations
- **Handle errors gracefully** with user feedback
