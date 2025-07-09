using System.Windows;

namespace SwappC
{
    public partial class ConnectionDialog : Window
    {
        public string Host
        {
            get => txtHost.Text;
            set => txtHost.Text = value;
        }

        public int Port
        {
            get => int.TryParse(txtPort.Text, out int port) ? port : 22;
            set => txtPort.Text = value.ToString();
        }

        public string Username
        {
            get => txtUsername.Text;
            set => txtUsername.Text = value;
        }

        public string Password
        {
            get => txtPassword.Password;
            set => txtPassword.Password = value;
        }

        public bool SaveCredentials
        {
            get => chkSaveCredentials.IsChecked == true;
            set => chkSaveCredentials.IsChecked = value;
        }

        public ConnectionDialog()
        {
            try
            {
                InitializeComponent();
                txtPassword.Password = "swapp"; // Default password
            }
            catch (System.Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ConnectionDialog initialization error: {ex.Message}");
            }
        }

        private void BtnOK_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(Host) || string.IsNullOrWhiteSpace(Username))
                {
                    MessageBox.Show("Please enter both host and username.", "Missing Information",
                                  MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                DialogResult = true;
            }
            catch (System.Exception ex)
            {
                MessageBox.Show($"❌ CONNECTION DIALOG ERROR\n\nError: {ex.Message}", 
                              "Dialog Error", MessageBoxButton.OK, MessageBoxImage.Error);
                System.Diagnostics.Debug.WriteLine($"ConnectionDialog OK button error: {ex.Message}");
            }
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                DialogResult = false;
            }
            catch (System.Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ConnectionDialog cancel button error: {ex.Message}");
                // Still close the dialog even if there's an error
                DialogResult = false;
            }
        }
    }
} 