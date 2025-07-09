using System;
using System.Configuration;
using System.Data;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;

namespace SwappC
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            try
            {
                // Global exception handlers to prevent crashes
                AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
                DispatcherUnhandledException += App_DispatcherUnhandledException;
                TaskScheduler.UnobservedTaskException += TaskScheduler_UnobservedTaskException;
                
                base.OnStartup(e);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"❌ APPLICATION STARTUP FAILED\n\nError: {ex.Message}", 
                              "Startup Error", MessageBoxButton.OK, MessageBoxImage.Error);
                Shutdown(1);
            }
        }

        private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            try
            {
                var exception = e.ExceptionObject as Exception;
                string message = exception?.Message ?? "Unknown error occurred";
                
                System.Diagnostics.Debug.WriteLine($"Unhandled exception: {message}");
                
                if (!e.IsTerminating)
                {
                    MessageBox.Show($"⚠️ UNEXPECTED ERROR\n\nThe application encountered an error but will continue running:\n\n{message}", 
                                  "Application Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
                else
                {
                    MessageBox.Show($"❌ CRITICAL ERROR\n\nThe application must close due to a critical error:\n\n{message}", 
                                  "Critical Error", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch
            {
                // If even error handling fails, just write to debug
                System.Diagnostics.Debug.WriteLine("Critical error in exception handler");
            }
        }

        private void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            try
            {
                System.Diagnostics.Debug.WriteLine($"Dispatcher unhandled exception: {e.Exception.Message}");
                
                MessageBox.Show($"⚠️ UI ERROR HANDLED\n\nA UI error was caught and handled:\n\n{e.Exception.Message}\n\nThe application will continue running.", 
                              "UI Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                
                e.Handled = true; // Prevent application crash
            }
            catch
            {
                // If error handling fails, let the original exception continue
                e.Handled = false;
            }
        }

        private void TaskScheduler_UnobservedTaskException(object sender, UnobservedTaskExceptionEventArgs e)
        {
            try
            {
                System.Diagnostics.Debug.WriteLine($"Unobserved task exception: {e.Exception.Message}");
                
                // Mark as observed to prevent process termination
                e.SetObserved();
            }
            catch
            {
                // If error handling fails, just continue
            }
        }
    }
} 