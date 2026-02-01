import React, { useState } from 'react';
import { X, User, Bell, Mail, Shield, FileText, HelpCircle, Moon, Sun, ExternalLink, Check, Briefcase } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { Separator } from './ui/separator';
import { Switch } from './ui/switch';
import PushNotificationButton from './PushNotificationButton';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const MobileMenu = ({ open, onClose, onNavigate }) => {
  const { isDark, toggleTheme } = useTheme();

  if (!open) return null;

  const menuItems = [
    {
      section: 'Quick Links',
      items: [
        { id: 'jobs', label: 'Cheshire Jobs', icon: Briefcase, action: () => onNavigate('jobs'), highlight: true },
      ]
    },
    { 
      section: 'Account',
      items: [
        { id: 'subscribe', label: 'Subscribe to Newsletter', icon: Mail, action: () => onNavigate('subscribe') },
        { id: 'notifications', label: 'Push Notifications', icon: Bell, isNotification: true },
      ]
    },
    {
      section: 'Information',
      items: [
        { id: 'about', label: 'About Cheshire Today', icon: HelpCircle, action: () => onNavigate('about') },
        { id: 'contact', label: 'Contact Us', icon: User, href: 'mailto:news@cheshiretoday.co.uk' },
      ]
    },
    {
      section: 'Legal',
      items: [
        { id: 'privacy', label: 'Privacy Policy', icon: Shield, action: () => onNavigate('privacy') },
        { id: 'terms', label: 'Terms of Service', icon: FileText, action: () => onNavigate('terms') },
      ]
    },
    {
      section: 'Follow Us',
      items: [
        { id: 'facebook', label: 'Facebook', icon: ExternalLink, href: 'https://www.facebook.com/865430919994962' },
        { id: 'twitter', label: 'Twitter / X', icon: ExternalLink, href: 'https://twitter.com/CheshireToday' },
      ]
    }
  ];

  return (
    <div className="fixed inset-0 z-[100] md:hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      
      {/* Menu Panel */}
      <div className="absolute right-0 top-0 bottom-0 w-[85%] max-w-sm bg-white dark:bg-gray-900 shadow-xl overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">Menu</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
            data-testid="mobile-menu-close"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Dark Mode Toggle */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isDark ? <Moon className="h-5 w-5 text-[#1E3A8A]" /> : <Sun className="h-5 w-5 text-amber-500" />}
              <span className="font-medium text-gray-900 dark:text-white">Dark Mode</span>
            </div>
            <Switch
              checked={isDark}
              onCheckedChange={toggleTheme}
              data-testid="dark-mode-toggle"
            />
          </div>
        </div>

        {/* Menu Sections */}
        <div className="pb-20">
          {menuItems.map((section, sectionIdx) => (
            <div key={section.section}>
              <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800">
                <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {section.section}
                </span>
              </div>
              {section.items.map((item) => {
                const Icon = item.icon;
                
                // Special handling for notifications - use actual PushNotificationButton
                if (item.isNotification) {
                  return (
                    <div
                      key={item.id}
                      className="flex items-center justify-between px-4 py-3 text-gray-700 dark:text-gray-300"
                      data-testid={`menu-item-${item.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <Bell className="h-5 w-5 text-gray-400" />
                        <span>{item.label}</span>
                      </div>
                      <PushNotificationButton apiUrl={API_URL} compact={true} />
                    </div>
                  );
                }
                
                if (item.href) {
                  return (
                    <a
                      key={item.id}
                      href={item.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                      data-testid={`menu-item-${item.id}`}
                    >
                      <Icon className="h-5 w-5 text-gray-400" />
                      <span>{item.label}</span>
                      <ExternalLink className="h-4 w-4 text-gray-400 ml-auto" />
                    </a>
                  );
                }
                
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      item.action?.();
                      onClose();
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 ${
                      item.highlight 
                        ? 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' 
                        : 'text-gray-700 dark:text-gray-300'
                    }`}
                    data-testid={`menu-item-${item.id}`}
                  >
                    <Icon className={`h-5 w-5 ${item.highlight ? 'text-emerald-600' : 'text-gray-400'}`} />
                    <span className={item.highlight ? 'font-medium' : ''}>{item.label}</span>
                    {item.highlight && (
                      <span className="ml-auto text-xs bg-emerald-600 text-white px-2 py-0.5 rounded-full">New</span>
                    )}
                  </button>
                );
              })}
              {sectionIdx < menuItems.length - 1 && <Separator />}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-center text-gray-500 dark:text-gray-400">
            © 2026 Cheshire Today. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MobileMenu;
