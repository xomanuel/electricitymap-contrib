import React, { useState, useEffect } from 'react';

import { useTranslation } from '../helpers/translation';

import Icon from './icon';

const Modal = ({ views, visible, onModalShown, onDismiss }) => {
  const { __ } = useTranslation();

  const [currentViewIndex, setCurrentViewIndex] = useState(0);
  const isOnLastView = () => currentViewIndex === views.length - 1;
  const isOnFirstView = () => currentViewIndex === 0;

  const handleBack = () => {
    if (!isOnFirstView()) {
      setCurrentViewIndex(currentViewIndex - 1);
    }
  };
  const handleForward = () => {
    if (!isOnLastView()) {
      setCurrentViewIndex(currentViewIndex + 1);
    }
  };

  // Dismiss the modal if SPACE key is pressed
  useEffect(() => {
    const keyPressHandlers = (ev) => {
      if (ev.keyCode === 32) {
        onDismiss();
      }
    };
    document.addEventListener('keypress', keyPressHandlers);
    return () => {
      document.removeEventListener('keypress', keyPressHandlers);
    };
  });

  // Track event when the onboarding modal opens up
  useEffect(() => {
    if (visible && onModalShown) {
      onModalShown();
    }
  }, [visible, onModalShown]);

  if (!visible) {
    return null;
  }

  const currentView = views[currentViewIndex];

  return (
    <React.Fragment>
      <div className="modal-background-overlay" onClick={onDismiss} />
      <div className="modal" data-test-id="onboarding">
        <div className="modal-left-button-container">
          {!isOnFirstView() && (
            <div className="modal-left-button" onClick={handleBack}>
              <Icon iconName="arrow_back" />
            </div>
          )}
        </div>
        <div className="modal-body">
          <div className="modal-close-button-container">
            <div className="modal-close-button" onClick={onDismiss}>
              <Icon iconName="close" />
            </div>
          </div>
          <div
            className={`modal-header ${currentView.headerCssClass || ''}`}
            style={{ backgroundImage: `url("${currentView.headerImage}")` }}
          />
          <div className={`modal-text ${currentView.textCssClass || ''}`}>{currentView.renderContent(__)}</div>
        </div>
        <div className="modal-footer">
          {views.map((view, index) => (
            <div
              key={`modal-step-item-${index}`}
              className={`modal-footer-circle ${index === currentViewIndex ? 'highlight' : ''}`}
            />
          ))}
        </div>
        <div className="modal-right-button-container">
          {isOnLastView() ? (
            <div className="modal-right-button green" onClick={onDismiss}>
              <Icon iconName="check" />
            </div>
          ) : (
            <div className="modal-right-button" onClick={handleForward}>
              <Icon iconName="arrow_forward" />
            </div>
          )}
        </div>
      </div>
    </React.Fragment>
  );
};

export default Modal;