// components/common/Button.js
import React from 'react';

const variants = {
  primary: 'bg-blue-500 hover:bg-blue-600 text-white',
  success: 'bg-green-500 hover:bg-green-600 text-white',
  danger: 'bg-red-500 hover:bg-red-600 text-white',
};

const Button = ({
  children,
  className = '',
  variant = 'primary',
  disabled = false,
  ...props
}) => {
  return (
    <button
      className={`
        px-4 py-2 rounded-lg transition-colors
        ${variants[variant]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;