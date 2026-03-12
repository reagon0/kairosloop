namespace MillimarN1700TestCSharp
{
    partial class FrmN1700Test
    {
        /// <summary>
        /// Erforderliche Designervariable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Verwendete Ressourcen bereinigen.
        /// </summary>
        /// <param name="disposing">True, wenn verwaltete Ressourcen gelöscht werden sollen; andernfalls False.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Vom Windows Form-Designer generierter Code

        /// <summary>
        /// Erforderliche Methode für die Designerunterstützung.
        /// Der Inhalt der Methode darf nicht mit dem Code-Editor geändert werden.
        /// </summary>
        private void InitializeComponent()
        {
            this.PnlTop = new System.Windows.Forms.Panel();
            this.TextBoxPollDataVal = new System.Windows.Forms.TextBox();
            this.ComboBoxPollDataChannel = new System.Windows.Forms.ComboBox();
            this.ButtonPollDataChannel = new System.Windows.Forms.Button();
            this.BtnGetCalib = new System.Windows.Forms.Button();
            this.BtnMeasure = new System.Windows.Forms.Button();
            this.label1 = new System.Windows.Forms.Label();
            this.PnlLedSwitch = new System.Windows.Forms.Panel();
            this.label3 = new System.Windows.Forms.Label();
            this.LblValsSec = new System.Windows.Forms.Label();
            this.LblVersion = new System.Windows.Forms.Label();
            this.LblVerTxt = new System.Windows.Forms.Label();
            this.PnlLedUsbStick = new System.Windows.Forms.Panel();
            this.dataGridView = new System.Windows.Forms.DataGridView();
            this.ColChannel = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ColModuleType = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ColDescription = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ColIdentNo = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ColSerialNo = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ColValue = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Velocity = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Multiturn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.BtnGetConfigVSS = new System.Windows.Forms.Button();
            this.PnlTop.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView)).BeginInit();
            this.SuspendLayout();
            // 
            // PnlTop
            // 
            this.PnlTop.Controls.Add(this.BtnGetConfigVSS);
            this.PnlTop.Controls.Add(this.TextBoxPollDataVal);
            this.PnlTop.Controls.Add(this.ComboBoxPollDataChannel);
            this.PnlTop.Controls.Add(this.ButtonPollDataChannel);
            this.PnlTop.Controls.Add(this.BtnGetCalib);
            this.PnlTop.Controls.Add(this.BtnMeasure);
            this.PnlTop.Controls.Add(this.label1);
            this.PnlTop.Controls.Add(this.PnlLedSwitch);
            this.PnlTop.Controls.Add(this.label3);
            this.PnlTop.Controls.Add(this.LblValsSec);
            this.PnlTop.Controls.Add(this.LblVersion);
            this.PnlTop.Controls.Add(this.LblVerTxt);
            this.PnlTop.Controls.Add(this.PnlLedUsbStick);
            this.PnlTop.Dock = System.Windows.Forms.DockStyle.Top;
            this.PnlTop.Location = new System.Drawing.Point(0, 0);
            this.PnlTop.Name = "PnlTop";
            this.PnlTop.Size = new System.Drawing.Size(827, 99);
            this.PnlTop.TabIndex = 2;
            // 
            // TextBoxPollDataVal
            // 
            this.TextBoxPollDataVal.Location = new System.Drawing.Point(297, 65);
            this.TextBoxPollDataVal.Name = "TextBoxPollDataVal";
            this.TextBoxPollDataVal.ReadOnly = true;
            this.TextBoxPollDataVal.Size = new System.Drawing.Size(100, 20);
            this.TextBoxPollDataVal.TabIndex = 21;
            // 
            // ComboBoxPollDataChannel
            // 
            this.ComboBoxPollDataChannel.FormattingEnabled = true;
            this.ComboBoxPollDataChannel.Location = new System.Drawing.Point(239, 65);
            this.ComboBoxPollDataChannel.Name = "ComboBoxPollDataChannel";
            this.ComboBoxPollDataChannel.Size = new System.Drawing.Size(46, 21);
            this.ComboBoxPollDataChannel.TabIndex = 20;
            // 
            // ButtonPollDataChannel
            // 
            this.ButtonPollDataChannel.Location = new System.Drawing.Point(80, 65);
            this.ButtonPollDataChannel.Name = "ButtonPollDataChannel";
            this.ButtonPollDataChannel.Size = new System.Drawing.Size(141, 23);
            this.ButtonPollDataChannel.TabIndex = 19;
            this.ButtonPollDataChannel.Text = "Poll Data from Channel:";
            this.ButtonPollDataChannel.UseVisualStyleBackColor = true;
            this.ButtonPollDataChannel.Click += new System.EventHandler(this.ButtonPollDataChannel_Click);
            // 
            // BtnGetCalib
            // 
            this.BtnGetCalib.Location = new System.Drawing.Point(494, 62);
            this.BtnGetCalib.Name = "BtnGetCalib";
            this.BtnGetCalib.Size = new System.Drawing.Size(151, 23);
            this.BtnGetCalib.TabIndex = 18;
            this.BtnGetCalib.Text = "Get Customer Calibration";
            this.BtnGetCalib.UseVisualStyleBackColor = true;
            this.BtnGetCalib.Click += new System.EventHandler(this.BtnGetCalib_Click);
            // 
            // BtnMeasure
            // 
            this.BtnMeasure.Location = new System.Drawing.Point(80, 15);
            this.BtnMeasure.Name = "BtnMeasure";
            this.BtnMeasure.Size = new System.Drawing.Size(141, 23);
            this.BtnMeasure.TabIndex = 17;
            this.BtnMeasure.Text = "Start Measuring";
            this.BtnMeasure.UseVisualStyleBackColor = true;
            this.BtnMeasure.Click += new System.EventHandler(this.BtnMeasure_Click);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(519, 21);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(39, 13);
            this.label1.TabIndex = 16;
            this.label1.Text = "Switch";
            // 
            // PnlLedSwitch
            // 
            this.PnlLedSwitch.BackColor = System.Drawing.Color.Gray;
            this.PnlLedSwitch.Location = new System.Drawing.Point(494, 18);
            this.PnlLedSwitch.Name = "PnlLedSwitch";
            this.PnlLedSwitch.Size = new System.Drawing.Size(19, 19);
            this.PnlLedSwitch.TabIndex = 15;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(294, 22);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(66, 13);
            this.label3.TabIndex = 14;
            this.label3.Text = "Values/Sec.";
            // 
            // LblValsSec
            // 
            this.LblValsSec.AutoSize = true;
            this.LblValsSec.Location = new System.Drawing.Point(252, 20);
            this.LblValsSec.Name = "LblValsSec";
            this.LblValsSec.Size = new System.Drawing.Size(16, 13);
            this.LblValsSec.TabIndex = 13;
            this.LblValsSec.Text = "...";
            this.LblValsSec.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // LblVersion
            // 
            this.LblVersion.AutoSize = true;
            this.LblVersion.Location = new System.Drawing.Point(664, 20);
            this.LblVersion.Name = "LblVersion";
            this.LblVersion.Size = new System.Drawing.Size(16, 13);
            this.LblVersion.TabIndex = 4;
            this.LblVersion.Text = "...";
            this.LblVersion.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // LblVerTxt
            // 
            this.LblVerTxt.AutoSize = true;
            this.LblVerTxt.Location = new System.Drawing.Point(593, 21);
            this.LblVerTxt.Name = "LblVerTxt";
            this.LblVerTxt.Size = new System.Drawing.Size(65, 13);
            this.LblVerTxt.TabIndex = 3;
            this.LblVerTxt.Text = "DLL-Version";
            this.LblVerTxt.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // PnlLedUsbStick
            // 
            this.PnlLedUsbStick.BackColor = System.Drawing.Color.Gray;
            this.PnlLedUsbStick.Location = new System.Drawing.Point(11, 18);
            this.PnlLedUsbStick.Name = "PnlLedUsbStick";
            this.PnlLedUsbStick.Size = new System.Drawing.Size(19, 19);
            this.PnlLedUsbStick.TabIndex = 0;
            // 
            // dataGridView
            // 
            this.dataGridView.AccessibleRole = System.Windows.Forms.AccessibleRole.TitleBar;
            this.dataGridView.AllowUserToAddRows = false;
            this.dataGridView.AllowUserToDeleteRows = false;
            this.dataGridView.AllowUserToResizeRows = false;
            this.dataGridView.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dataGridView.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.ColChannel,
            this.ColModuleType,
            this.ColDescription,
            this.ColIdentNo,
            this.ColSerialNo,
            this.ColValue,
            this.Velocity,
            this.Multiturn});
            this.dataGridView.Dock = System.Windows.Forms.DockStyle.Fill;
            this.dataGridView.EditMode = System.Windows.Forms.DataGridViewEditMode.EditProgrammatically;
            this.dataGridView.Location = new System.Drawing.Point(0, 99);
            this.dataGridView.MultiSelect = false;
            this.dataGridView.Name = "dataGridView";
            this.dataGridView.ReadOnly = true;
            this.dataGridView.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.dataGridView.ShowCellToolTips = false;
            this.dataGridView.ShowEditingIcon = false;
            this.dataGridView.Size = new System.Drawing.Size(827, 455);
            this.dataGridView.TabIndex = 10;
            this.dataGridView.CellContentClick += new System.Windows.Forms.DataGridViewCellEventHandler(this.dataGridView_CellContentClick);
            // 
            // ColChannel
            // 
            this.ColChannel.HeaderText = "Channel";
            this.ColChannel.Name = "ColChannel";
            this.ColChannel.ReadOnly = true;
            this.ColChannel.Width = 71;
            // 
            // ColModuleType
            // 
            this.ColModuleType.HeaderText = "sModuleType";
            this.ColModuleType.Name = "ColModuleType";
            this.ColModuleType.ReadOnly = true;
            this.ColModuleType.Width = 120;
            // 
            // ColDescription
            // 
            this.ColDescription.HeaderText = "sDescription";
            this.ColDescription.Name = "ColDescription";
            this.ColDescription.ReadOnly = true;
            this.ColDescription.Width = 120;
            // 
            // ColIdentNo
            // 
            this.ColIdentNo.HeaderText = "sIdentNo";
            this.ColIdentNo.Name = "ColIdentNo";
            this.ColIdentNo.ReadOnly = true;
            this.ColIdentNo.Width = 75;
            // 
            // ColSerialNo
            // 
            this.ColSerialNo.HeaderText = "sSerialNo";
            this.ColSerialNo.Name = "ColSerialNo";
            this.ColSerialNo.ReadOnly = true;
            this.ColSerialNo.Width = 77;
            // 
            // ColValue
            // 
            this.ColValue.HeaderText = "Value";
            this.ColValue.Name = "ColValue";
            this.ColValue.ReadOnly = true;
            // 
            // Velocity
            // 
            this.Velocity.HeaderText = "Velocity";
            this.Velocity.Name = "Velocity";
            this.Velocity.ReadOnly = true;
            // 
            // Multiturn
            // 
            this.Multiturn.HeaderText = "MultiTurn";
            this.Multiturn.Name = "Multiturn";
            this.Multiturn.ReadOnly = true;
            // 
            // BtnGetConfigVSS
            // 
            this.BtnGetConfigVSS.Location = new System.Drawing.Point(651, 62);
            this.BtnGetConfigVSS.Name = "BtnGetConfigVSS";
            this.BtnGetConfigVSS.Size = new System.Drawing.Size(151, 23);
            this.BtnGetConfigVSS.TabIndex = 22;
            this.BtnGetConfigVSS.Text = "Get Config VSS Channel 1";
            this.BtnGetConfigVSS.UseVisualStyleBackColor = true;
            this.BtnGetConfigVSS.Click += new System.EventHandler(this.BtnGetConfigVSS_Click);
            // 
            // FrmN1700Test
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(827, 554);
            this.Controls.Add(this.dataGridView);
            this.Controls.Add(this.PnlTop);
            this.Name = "FrmN1700Test";
            this.Text = "N1700-Test";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.FrmN1700Test_FormClosing);
            this.Load += new System.EventHandler(this.FrmN1700Test_Load);
            this.PnlTop.ResumeLayout(false);
            this.PnlTop.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dataGridView)).EndInit();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Panel PnlTop;
        private System.Windows.Forms.Label LblVersion;
        private System.Windows.Forms.Label LblVerTxt;
        private System.Windows.Forms.Panel PnlLedUsbStick;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label LblValsSec;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Panel PnlLedSwitch;
        private System.Windows.Forms.DataGridView dataGridView;
        private System.Windows.Forms.Button BtnMeasure;
        private System.Windows.Forms.Button BtnGetCalib;
        private System.Windows.Forms.TextBox TextBoxPollDataVal;
        private System.Windows.Forms.ComboBox ComboBoxPollDataChannel;
        private System.Windows.Forms.Button ButtonPollDataChannel;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColChannel;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColModuleType;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColDescription;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColIdentNo;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColSerialNo;
        private System.Windows.Forms.DataGridViewTextBoxColumn ColValue;
        private System.Windows.Forms.DataGridViewTextBoxColumn Velocity;
        private System.Windows.Forms.DataGridViewTextBoxColumn Multiturn;
        private System.Windows.Forms.Button BtnGetConfigVSS;
    }
}

