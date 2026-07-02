import React, { useState, useEffect, useRef } from 'react';

export default function CustomDropdown({
  options,
  value,
  onChange,
  placeholder = '-- Select --',
  disabled = false,
  style = {},
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Toggle dropdown visibility
  const toggleDropdown = () => {
    if (!disabled) {
      setIsOpen((prev) => !prev);
    }
  };

  // Close when clicking outside the dropdown container
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Close when pressing Escape key
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Find the selected option label
  const selectedOption = options.find((opt) => String(opt.value) === String(value));
  const displayText = selectedOption ? selectedOption.label : placeholder;

  const handleOptionClick = (val) => {
    onChange({ target: { value: val } });
    setIsOpen(false);
  };

  return (
    <div
      ref={dropdownRef}
      className={`custom-dropdown ${className}`}
      style={{ ...style }}
    >
      <button
        type="button"
        className={`custom-dropdown-trigger ${isOpen ? 'open' : ''}`}
        onClick={toggleDropdown}
        disabled={disabled}
      >
        <span>{displayText}</span>
        <svg
          className="custom-dropdown-arrow"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="custom-dropdown-menu">
          {options.map((option) => (
            <div
              key={option.value}
              className={`custom-dropdown-item ${String(option.value) === String(value) ? 'selected' : ''}`}
              onClick={() => handleOptionClick(option.value)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
