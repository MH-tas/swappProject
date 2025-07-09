namespace CiscoSNMPMonitor
{
    partial class MainForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.Windows.Forms.DataVisualization.Charting.ChartArea chartArea1 = new System.Windows.Forms.DataVisualization.Charting.ChartArea();
            System.Windows.Forms.DataVisualization.Charting.Legend legend1 = new System.Windows.Forms.DataVisualization.Charting.Legend();
            System.Windows.Forms.DataVisualization.Charting.ChartArea chartArea2 = new System.Windows.Forms.DataVisualization.Charting.ChartArea();
            System.Windows.Forms.DataVisualization.Charting.Legend legend2 = new System.Windows.Forms.DataVisualization.Charting.Legend();
            System.Windows.Forms.DataVisualization.Charting.ChartArea chartArea3 = new System.Windows.Forms.DataVisualization.Charting.ChartArea();
            System.Windows.Forms.DataVisualization.Charting.Legend legend3 = new System.Windows.Forms.DataVisualization.Charting.Legend();

            this.components = new System.ComponentModel.Container();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.txtCommunity = new System.Windows.Forms.TextBox();
            this.label3 = new System.Windows.Forms.Label();
            this.txtPort = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.txtIP = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.btnTest = new System.Windows.Forms.Button();
            this.btnConnect = new System.Windows.Forms.Button();
            this.systemNameLabel = new System.Windows.Forms.Label();
            this.systemDescTextBox = new System.Windows.Forms.TextBox();
            this.interfaceListView = new System.Windows.Forms.ListView();
            this.statusStrip = new System.Windows.Forms.StatusStrip();
            this.statusLabel = new System.Windows.Forms.ToolStripStatusLabel();
            this.autoRefreshCheckBox = new System.Windows.Forms.CheckBox();
            this.refreshIntervalNumeric = new System.Windows.Forms.NumericUpDown();
            this.label4 = new System.Windows.Forms.Label();
            this.uptimeLabel = new System.Windows.Forms.Label();
            this.locationLabel = new System.Windows.Forms.Label();
            this.contactLabel = new System.Windows.Forms.Label();
            this.cpuChart = new System.Windows.Forms.DataVisualization.Charting.Chart();
            this.memoryChart = new System.Windows.Forms.DataVisualization.Charting.Chart();
            this.trafficChart = new System.Windows.Forms.DataVisualization.Charting.Chart();
            this.temperatureLabel = new System.Windows.Forms.Label();
            this.fanStatusLabel = new System.Windows.Forms.Label();
            this.powerStatusLabel = new System.Windows.Forms.Label();
            this.groupBox2 = new System.Windows.Forms.GroupBox();
            this.groupBox3 = new System.Windows.Forms.GroupBox();
            this.groupBox4 = new System.Windows.Forms.GroupBox();

            // groupBox1
            this.groupBox1.Controls.Add(this.txtCommunity);
            this.groupBox1.Controls.Add(this.label3);
            this.groupBox1.Controls.Add(this.txtPort);
            this.groupBox1.Controls.Add(this.label2);
            this.groupBox1.Controls.Add(this.txtIP);
            this.groupBox1.Controls.Add(this.label1);
            this.groupBox1.Controls.Add(this.btnTest);
            this.groupBox1.Controls.Add(this.btnConnect);
            this.groupBox1.Location = new System.Drawing.Point(12, 12);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(978, 65);
            this.groupBox1.TabIndex = 0;
            this.groupBox1.Text = "Bağlantı Ayarları";

            // txtCommunity
            this.txtCommunity.Location = new System.Drawing.Point(485, 25);
            this.txtCommunity.Name = "txtCommunity";
            this.txtCommunity.Size = new System.Drawing.Size(100, 23);
            this.txtCommunity.TabIndex = 5;
            this.txtCommunity.Text = "swapp";

            // label3
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(410, 28);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(69, 15);
            this.label3.TabIndex = 4;
            this.label3.Text = "Community:";

            // txtPort
            this.txtPort.Location = new System.Drawing.Point(304, 25);
            this.txtPort.Name = "txtPort";
            this.txtPort.Size = new System.Drawing.Size(100, 23);
            this.txtPort.TabIndex = 3;
            this.txtPort.Text = "161";

            // label2
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(266, 28);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(32, 15);
            this.label2.TabIndex = 2;
            this.label2.Text = "Port:";

            // txtIP
            this.txtIP.Location = new System.Drawing.Point(100, 25);
            this.txtIP.Name = "txtIP";
            this.txtIP.Size = new System.Drawing.Size(160, 23);
            this.txtIP.TabIndex = 1;
            this.txtIP.Text = "192.168.20.1";

            // label1
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(20, 28);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(74, 15);
            this.label1.TabIndex = 0;
            this.label1.Text = "IP Adresi:";

            // btnTest
            this.btnTest.Location = new System.Drawing.Point(591, 24);
            this.btnTest.Name = "btnTest";
            this.btnTest.Size = new System.Drawing.Size(180, 25);
            this.btnTest.TabIndex = 6;
            this.btnTest.Text = "BAĞLANTIYI TEST ET";
            this.btnTest.UseVisualStyleBackColor = true;

            // btnConnect
            this.btnConnect.Location = new System.Drawing.Point(777, 24);
            this.btnConnect.Name = "btnConnect";
            this.btnConnect.Size = new System.Drawing.Size(180, 25);
            this.btnConnect.TabIndex = 7;
            this.btnConnect.Text = "BAĞLAN";
            this.btnConnect.UseVisualStyleBackColor = true;
            this.btnConnect.BackColor = System.Drawing.Color.FromArgb(0, 122, 204);
            this.btnConnect.ForeColor = System.Drawing.Color.White;

            // systemNameLabel
            this.systemNameLabel.AutoSize = true;
            this.systemNameLabel.Font = new System.Drawing.Font("Segoe UI", 12F, System.Drawing.FontStyle.Bold);
            this.systemNameLabel.Location = new System.Drawing.Point(12, 90);
            this.systemNameLabel.Name = "systemNameLabel";
            this.systemNameLabel.Size = new System.Drawing.Size(89, 21);
            this.systemNameLabel.TabIndex = 8;
            this.systemNameLabel.Text = "Switch Adı";

            // systemDescTextBox
            this.systemDescTextBox.Location = new System.Drawing.Point(12, 115);
            this.systemDescTextBox.Multiline = true;
            this.systemDescTextBox.Name = "systemDescTextBox";
            this.systemDescTextBox.ReadOnly = true;
            this.systemDescTextBox.Size = new System.Drawing.Size(978, 40);
            this.systemDescTextBox.TabIndex = 9;

            // interfaceListView
            this.interfaceListView.FullRowSelect = true;
            this.interfaceListView.GridLines = true;
            this.interfaceListView.Location = new System.Drawing.Point(12, 255);
            this.interfaceListView.Name = "interfaceListView";
            this.interfaceListView.Size = new System.Drawing.Size(978, 294);
            this.interfaceListView.TabIndex = 10;
            this.interfaceListView.UseCompatibleStateImageBehavior = false;
            this.interfaceListView.View = System.Windows.Forms.View.Details;

            // statusStrip
            this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] { this.statusLabel });
            this.statusStrip.Location = new System.Drawing.Point(0, 589);
            this.statusStrip.Name = "statusStrip";
            this.statusStrip.Size = new System.Drawing.Size(1002, 22);
            this.statusStrip.TabIndex = 11;

            // statusLabel
            this.statusLabel.Name = "statusLabel";
            this.statusLabel.Size = new System.Drawing.Size(39, 17);
            this.statusLabel.Text = "Hazır";

            // autoRefreshCheckBox
            this.autoRefreshCheckBox.AutoSize = true;
            this.autoRefreshCheckBox.Location = new System.Drawing.Point(12, 561);
            this.autoRefreshCheckBox.Name = "autoRefreshCheckBox";
            this.autoRefreshCheckBox.Size = new System.Drawing.Size(108, 19);
            this.autoRefreshCheckBox.TabIndex = 12;
            this.autoRefreshCheckBox.Text = "Otomatik Yenile";

            // refreshIntervalNumeric
            this.refreshIntervalNumeric.Location = new System.Drawing.Point(126, 560);
            this.refreshIntervalNumeric.Maximum = new decimal(new int[] { 3600, 0, 0, 0 });
            this.refreshIntervalNumeric.Minimum = new decimal(new int[] { 1, 0, 0, 0 });
            this.refreshIntervalNumeric.Name = "refreshIntervalNumeric";
            this.refreshIntervalNumeric.Size = new System.Drawing.Size(60, 23);
            this.refreshIntervalNumeric.TabIndex = 13;
            this.refreshIntervalNumeric.Value = new decimal(new int[] { 5, 0, 0, 0 });

            // label4
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(192, 562);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(43, 15);
            this.label4.TabIndex = 14;
            this.label4.Text = "saniye";

            // uptimeLabel
            this.uptimeLabel.AutoSize = true;
            this.uptimeLabel.Location = new System.Drawing.Point(12, 165);
            this.uptimeLabel.Name = "uptimeLabel";
            this.uptimeLabel.Size = new System.Drawing.Size(54, 15);
            this.uptimeLabel.TabIndex = 15;
            this.uptimeLabel.Text = "Uptime: -";

            // locationLabel
            this.locationLabel.AutoSize = true;
            this.locationLabel.Location = new System.Drawing.Point(12, 185);
            this.locationLabel.Name = "locationLabel";
            this.locationLabel.Size = new System.Drawing.Size(54, 15);
            this.locationLabel.TabIndex = 16;
            this.locationLabel.Text = "Konum: -";

            // contactLabel
            this.contactLabel.AutoSize = true;
            this.contactLabel.Location = new System.Drawing.Point(12, 205);
            this.contactLabel.Name = "contactLabel";
            this.contactLabel.Size = new System.Drawing.Size(60, 15);
            this.contactLabel.TabIndex = 17;
            this.contactLabel.Text = "İletişim: -";

            // groupBox2 - CPU ve Bellek
            this.groupBox2.Text = "Sistem Metrikleri";
            this.groupBox2.Location = new System.Drawing.Point(250, 165);
            this.groupBox2.Size = new System.Drawing.Size(240, 80);
            this.groupBox2.Controls.Add(this.cpuChart);
            this.groupBox2.Controls.Add(this.memoryChart);

            // cpuChart
            this.cpuChart.ChartAreas.Add(chartArea1);
            this.cpuChart.Legends.Add(legend1);
            this.cpuChart.Location = new System.Drawing.Point(10, 20);
            this.cpuChart.Size = new System.Drawing.Size(100, 50);
            this.cpuChart.Titles.Add("CPU");

            // memoryChart
            this.memoryChart.ChartAreas.Add(chartArea2);
            this.memoryChart.Legends.Add(legend2);
            this.memoryChart.Location = new System.Drawing.Point(130, 20);
            this.memoryChart.Size = new System.Drawing.Size(100, 50);
            this.memoryChart.Titles.Add("Bellek");

            // groupBox3 - Trafik
            this.groupBox3.Text = "Port 1 Trafik";
            this.groupBox3.Location = new System.Drawing.Point(500, 165);
            this.groupBox3.Size = new System.Drawing.Size(240, 80);
            this.groupBox3.Controls.Add(this.trafficChart);

            // trafficChart
            this.trafficChart.ChartAreas.Add(chartArea3);
            this.trafficChart.Legends.Add(legend3);
            this.trafficChart.Location = new System.Drawing.Point(10, 20);
            this.trafficChart.Size = new System.Drawing.Size(220, 50);
            this.trafficChart.Titles.Add("Trafik");

            // groupBox4 - Donanım Durumu
            this.groupBox4.Text = "Donanım Durumu";
            this.groupBox4.Location = new System.Drawing.Point(750, 165);
            this.groupBox4.Size = new System.Drawing.Size(240, 80);
            this.groupBox4.Controls.Add(this.temperatureLabel);
            this.groupBox4.Controls.Add(this.fanStatusLabel);
            this.groupBox4.Controls.Add(this.powerStatusLabel);

            // temperatureLabel
            this.temperatureLabel.Location = new System.Drawing.Point(10, 20);
            this.temperatureLabel.Text = "Sıcaklık: -";

            // fanStatusLabel
            this.fanStatusLabel.Location = new System.Drawing.Point(10, 40);
            this.fanStatusLabel.Text = "Fan Durumu: -";

            // powerStatusLabel
            this.powerStatusLabel.Location = new System.Drawing.Point(10, 60);
            this.powerStatusLabel.Text = "Güç Durumu: -";

            // MainForm
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1002, 611);
            this.Controls.Add(this.groupBox4);
            this.Controls.Add(this.groupBox3);
            this.Controls.Add(this.groupBox2);
            this.Controls.Add(this.contactLabel);
            this.Controls.Add(this.locationLabel);
            this.Controls.Add(this.uptimeLabel);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.refreshIntervalNumeric);
            this.Controls.Add(this.autoRefreshCheckBox);
            this.Controls.Add(this.statusStrip);
            this.Controls.Add(this.interfaceListView);
            this.Controls.Add(this.systemDescTextBox);
            this.Controls.Add(this.systemNameLabel);
            this.Controls.Add(this.groupBox1);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Name = "MainForm";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Cisco Switch Monitor";
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            this.statusStrip.ResumeLayout(false);
            this.statusStrip.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.refreshIntervalNumeric)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.cpuChart)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.memoryChart)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.trafficChart)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();
        }

        #endregion

        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.TextBox txtCommunity;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.TextBox txtPort;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox txtIP;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Button btnTest;
        private System.Windows.Forms.Button btnConnect;
        private System.Windows.Forms.Label systemNameLabel;
        private System.Windows.Forms.TextBox systemDescTextBox;
        private System.Windows.Forms.ListView interfaceListView;
        private System.Windows.Forms.StatusStrip statusStrip;
        private System.Windows.Forms.ToolStripStatusLabel statusLabel;
        private System.Windows.Forms.CheckBox autoRefreshCheckBox;
        private System.Windows.Forms.NumericUpDown refreshIntervalNumeric;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.Label uptimeLabel;
        private System.Windows.Forms.Label locationLabel;
        private System.Windows.Forms.Label contactLabel;
        private System.Windows.Forms.DataVisualization.Charting.Chart cpuChart;
        private System.Windows.Forms.DataVisualization.Charting.Chart memoryChart;
        private System.Windows.Forms.DataVisualization.Charting.Chart trafficChart;
        private System.Windows.Forms.Label temperatureLabel;
        private System.Windows.Forms.Label fanStatusLabel;
        private System.Windows.Forms.Label powerStatusLabel;
        private System.Windows.Forms.GroupBox groupBox2;
        private System.Windows.Forms.GroupBox groupBox3;
        private System.Windows.Forms.GroupBox groupBox4;
    }
} 